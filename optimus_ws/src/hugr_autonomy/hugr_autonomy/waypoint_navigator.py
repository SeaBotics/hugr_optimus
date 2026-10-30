#!/usr/bin/env python3
"""
Autonomous Line-of-Sight (LOS) Waypoint Navigator for Hugr Optimus ASV
Implements:
 - Thor I. Fossen's LOS Guidance Law with cross-track error compensation (Fossen Chapter 10)
 - Heading Autopilot (PID Controller on Heading Error)
 - 4-Thruster Motor Allocation & Wave Correction Telemetry
 - Autonomous Buoy Competition Circuit Sequencer
 - Target (Planned) vs Actual (Followed) Path Visualizers
 - 3D Cross-Track Deviation Vector in RViz2
"""

import math
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped, Point
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import String, Empty, Float32, Float32MultiArray, Int32MultiArray
from visualization_msgs.msg import Marker, MarkerArray

class WaypointNavigatorNode(Node):
    # Pre-computed Competition Buoy Circuit:
    # Threads Gate 1 (Red & Green buoys), Gate 2, rounds the Yellow Pivot Buoy, and returns.
    COMPETITION_CIRCUIT = [
        {"name": "Gate 1 Center", "pos": [8.0, 0.0]},
        {"name": "Gate 2 Center", "pos": [18.0, 1.0]},
        {"name": "Approach Pivot Buoy", "pos": [24.5, 0.0]},
        {"name": "Orbit North (Yellow)", "pos": [28.0, 3.8]},
        {"name": "Orbit East (Yellow)", "pos": [32.0, 0.0]},
        {"name": "Orbit South (Yellow)", "pos": [28.0, -3.8]},
        {"name": "Return Gate 2", "pos": [18.0, 1.0]},
        {"name": "Return Gate 1", "pos": [8.0, 0.0]},
        {"name": "Home / Finish", "pos": [0.0, 0.0]}
    ]

    def __init__(self):
        super().__init__('waypoint_navigator')

        # Guidance parameters
        self.declare_parameter('guidance.lookahead_distance', 3.5)
        self.declare_parameter('guidance.acceptance_radius', 1.5)
        self.declare_parameter('guidance.cruise_speed', 1.2)

        # Heading autopilot parameters
        self.declare_parameter('heading_controller.kp', 1.8)
        self.declare_parameter('heading_controller.ki', 0.05)
        self.declare_parameter('heading_controller.kd', 0.6)
        self.declare_parameter('heading_controller.max_yaw_rate', 1.2)
        self.declare_parameter('heading_controller.integral_limit', 0.5)

        # Thruster geometry (moment arms from CAD)
        self.declare_parameter('thrusters.arm_y', 0.1518)
        self.declare_parameter('thrusters.arm_x_bow', 0.2884)
        self.declare_parameter('thrusters.arm_x_stern', 0.4066)

        # GPS Datum (Grimstad, Norway)
        self.declare_parameter('gnss.origin_latitude', 58.334000)
        self.declare_parameter('gnss.origin_longitude', 8.578000)

        self.delta = float(self.get_parameter('guidance.lookahead_distance').value)
        self.r_accept = float(self.get_parameter('guidance.acceptance_radius').value)
        self.cruise_speed = float(self.get_parameter('guidance.cruise_speed').value)

        self.kp = float(self.get_parameter('heading_controller.kp').value)
        self.ki = float(self.get_parameter('heading_controller.ki').value)
        self.kd = float(self.get_parameter('heading_controller.kd').value)
        self.max_w = float(self.get_parameter('heading_controller.max_yaw_rate').value)
        self.integral_limit = float(self.get_parameter('heading_controller.integral_limit').value)

        self.arm_y = float(self.get_parameter('thrusters.arm_y').value)
        self.arm_x_bow = float(self.get_parameter('thrusters.arm_x_bow').value)
        self.arm_x_stern = float(self.get_parameter('thrusters.arm_x_stern').value)

        self.lat_origin = float(self.get_parameter('gnss.origin_latitude').value)
        self.lon_origin = float(self.get_parameter('gnss.origin_longitude').value)
        self.R_EARTH = 6378137.0

        # Vessel state
        self.pos = np.zeros(2, dtype=float)
        self.psi = 0.0
        self.r = 0.0
        self.speed_u = 0.0
        self.odom_received = False

        # Mission & Waypoint queue
        self.waypoint_queue = []
        self.waypoint_names = []
        self.current_wp_idx = 0
        self.active_goal = None
        self.segment_start_pos = None

        # Tracking telemetry
        self.cross_track_error = 0.0
        self.heading_error = 0.0
        self.dist_to_goal = 0.0
        self.cmd_v = 0.0
        self.cmd_w = 0.0
        self.motor_pwms = [1500, 1500, 1500, 1500]

        # Trajectory history (actual path followed)
        self.actual_path_history = []
        self.last_path_record_pos = np.zeros(2, dtype=float)

        # Controller variables
        self.integral_error = 0.0
        self.last_heading_error = 0.0
        self.last_time = self.get_clock().now()
        self.last_log_time = 0.0

        # Status: IDLE, NAVIGATING, WAYPOINT_REACHED, MISSION_COMPLETED
        self.status = "IDLE"

        # Subscribers
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)
        self.goal_pose_sub = self.create_subscription(PoseStamped, '/goal_pose', self.goal_pose_callback, 10)
        self.goal_gps_sub = self.create_subscription(NavSatFix, '/destination_gps', self.goal_gps_callback, 10)
        self.circuit_sub = self.create_subscription(Empty, '/autonomous/start_circuit', self.start_circuit_callback, 10)
        self.cancel_sub = self.create_subscription(Empty, '/cancel_destination', self.cancel_callback, 10)

        # Publishers
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/autonomous/status', 10)
        self.planned_path_pub = self.create_publisher(Path, '/autonomous/planned_path', 10)
        self.actual_path_pub = self.create_publisher(Path, '/autonomous/actual_path', 10)
        self.cross_track_pub = self.create_publisher(Float32, '/autonomous/cross_track_error', 10)
        self.telemetry_pub = self.create_publisher(Float32MultiArray, '/autonomous/telemetry', 10)
        self.motor_pwms_pub = self.create_publisher(Int32MultiArray, '/autonomous/motor_pwms', 10)
        self.markers_pub = self.create_publisher(MarkerArray, '/autonomous/waypoint_markers', 10)
        self.cross_track_marker_pub = self.create_publisher(Marker, '/autonomous/cross_track_marker', 10)

        # Timers: Control loop at 20 Hz, Telemetry broadcast at 5 Hz
        self.control_timer = self.create_timer(0.05, self.control_loop)
        self.telemetry_timer = self.create_timer(0.2, self.publish_telemetry)

        self.get_logger().info('Autonomous LOS Waypoint Navigator & Circuit Planner initialized.')
        self.get_logger().info('Ready. Trigger Buoy Circuit via topic: /autonomous/start_circuit')

    def gps_to_metric(self, lat, lon):
        d_lat = math.radians(lat - self.lat_origin)
        d_lon = math.radians(lon - self.lon_origin)
        lat_ref_rad = math.radians(self.lat_origin)
        y_north = self.R_EARTH * d_lat
        x_east = self.R_EARTH * d_lon * math.cos(lat_ref_rad)
        return np.array([x_east, y_north], dtype=float)

    def metric_to_gps(self, x_east, y_north):
        lat_ref_rad = math.radians(self.lat_origin)
        lat = self.lat_origin + math.degrees(y_north / self.R_EARTH)
        lon = self.lon_origin + math.degrees(x_east / (self.R_EARTH * math.cos(lat_ref_rad)))
        return lat, lon

    def odom_callback(self, msg: Odometry):
        self.pos[0] = msg.pose.pose.position.x
        self.pos[1] = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.psi = math.atan2(siny_cosp, cosy_cosp)
        self.r = msg.twist.twist.angular.z
        self.speed_u = msg.twist.twist.linear.x
        self.odom_received = True

        # Record breadcrumb trail for actual path followed
        dist_since_last = np.linalg.norm(self.pos - self.last_path_record_pos)
        if dist_since_last > 0.25 and self.status == "NAVIGATING":
            self.last_path_record_pos = np.copy(self.pos)
            self.actual_path_history.append(np.copy(self.pos))
            if len(self.actual_path_history) > 2000:
                self.actual_path_history.pop(0)

    def start_circuit_callback(self, _=None):
        """Starts the full autonomous competition buoy circuit mission."""
        if not self.odom_received:
            self.get_logger().warn('Cannot start circuit: Odometry not received yet.')
            return

        wps = [item["pos"] for item in self.COMPETITION_CIRCUIT]
        names = [item["name"] for item in self.COMPETITION_CIRCUIT]
        self.get_logger().info(f'🏁 STARTING COMPETITION BUOY CIRCUIT ({len(wps)} Waypoints)...')
        self.set_mission(wps, names)

    def goal_pose_callback(self, msg: PoseStamped):
        target = np.array([msg.pose.position.x, msg.pose.position.y], dtype=float)
        lat, lon = self.metric_to_gps(target[0], target[1])
        self.get_logger().info(f'Received Metric Target: X={target[0]:.2f}m, Y={target[1]:.2f}m (GPS: {lat:.6f}, {lon:.6f})')
        self.set_mission([target], ["Custom Target"])

    def goal_gps_callback(self, msg: NavSatFix):
        target = self.gps_to_metric(msg.latitude, msg.longitude)
        self.get_logger().info(f'Received GPS Target: Lat={msg.latitude:.6f}, Lon={msg.longitude:.6f} -> Local: X={target[0]:.2f}m, Y={target[1]:.2f}m')
        self.set_mission([target], ["GPS Target"])

    def cancel_callback(self, _):
        self.get_logger().warn('Mission cancelled by operator! Stopping vessel.')
        self.stop_vessel()
        self.waypoint_queue = []
        self.active_goal = None
        self.status = "IDLE"
        self.publish_markers()
        self.publish_planned_path()

    def set_mission(self, waypoints, names=None):
        self.segment_start_pos = np.copy(self.pos)
        self.waypoint_queue = [np.array(wp, dtype=float) for wp in waypoints]
        self.waypoint_names = names if names is not None else [f"WP {i+1}" for i in range(len(waypoints))]
        self.current_wp_idx = 0
        self.active_goal = self.waypoint_queue[0]
        self.integral_error = 0.0
        self.status = "NAVIGATING"
        self.actual_path_history = [np.copy(self.pos)]
        self.last_path_record_pos = np.copy(self.pos)

        self.publish_markers()
        self.publish_planned_path()
        self.publish_actual_path()

    def control_loop(self):
        if not self.odom_received or self.active_goal is None:
            return

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now
        if dt <= 0.0 or dt > 0.5:
            dt = 0.05

        current_target = self.active_goal
        delta_vec = current_target - self.pos
        self.dist_to_goal = np.linalg.norm(delta_vec)

        # Check Waypoint Arrival Criteria
        if self.dist_to_goal < self.r_accept:
            wp_name = self.waypoint_names[self.current_wp_idx] if self.current_wp_idx < len(self.waypoint_names) else ""
            self.current_wp_idx += 1
            if self.current_wp_idx < len(self.waypoint_queue):
                self.segment_start_pos = np.copy(self.pos)
                self.active_goal = self.waypoint_queue[self.current_wp_idx]
                next_name = self.waypoint_names[self.current_wp_idx]
                self.integral_error = 0.0
                self.get_logger().info(f'✓ REACHED Waypoint {self.current_wp_idx}: {wp_name}! Heading to: {next_name} ({self.active_goal[0]:.1f}, {self.active_goal[1]:.1f})')
                self.publish_markers()
            else:
                self.get_logger().info(f'🏁 MISSION COMPLETED! All {len(self.waypoint_queue)} waypoints reached. Vessel stopping.')
                self.stop_vessel()
                self.active_goal = None
                self.status = "MISSION_COMPLETED"
                self.publish_markers()
                return

        # ================= Line-of-Sight (LOS) Guidance Law =================
        pk = self.segment_start_pos if self.segment_start_pos is not None else self.pos
        pk1 = current_target
        path_vec = pk1 - pk
        path_len = np.linalg.norm(path_vec)

        if path_len > 0.1:
            path_angle = math.atan2(path_vec[1], path_vec[0])
            # Cross-track error e: perpendicular distance from vessel to the straight-line segment
            # Positive e = vessel is to PORT (left) of the path
            # Negative e = vessel is to STARBOARD (right) of the path
            self.cross_track_error = -(self.pos[0] - pk[0]) * math.sin(path_angle) + (self.pos[1] - pk[1]) * math.cos(path_angle)
            
            # Along-track projection point on the line segment
            s = (self.pos[0] - pk[0]) * math.cos(path_angle) + (self.pos[1] - pk[1]) * math.sin(path_angle)
            s_clamped = max(0.0, min(path_len, s))
            proj_point = pk + s_clamped * np.array([math.cos(path_angle), math.sin(path_angle)])

            # Desired heading to converge onto the line (Thor Fossen Chapter 10)
            psi_desired = path_angle + math.atan2(-self.cross_track_error, self.delta)
        else:
            self.cross_track_error = 0.0
            proj_point = current_target
            psi_desired = math.atan2(delta_vec[1], delta_vec[0])

        # Heading error wrapped to [-pi, pi]
        self.heading_error = math.atan2(math.sin(psi_desired - self.psi), math.cos(psi_desired - self.psi))

        # ================= PID Heading Autopilot =================
        self.integral_error += self.heading_error * dt
        self.integral_error = np.clip(self.integral_error, -self.integral_limit, self.integral_limit)

        derivative = (self.heading_error - self.last_heading_error) / dt
        self.last_heading_error = self.heading_error

        self.cmd_w = self.kp * self.heading_error + self.ki * self.integral_error + self.kd * derivative
        self.cmd_w = np.clip(self.cmd_w, -self.max_w, self.max_w)

        # ================= Speed Controller =================
        # Prioritize turning when heading error is large
        turn_factor = max(0.2, math.cos(self.heading_error))
        # Smooth deceleration within arrival window
        dist_factor = min(1.0, max(0.35, self.dist_to_goal / (self.r_accept * 2.0)))
        self.cmd_v = self.cruise_speed * turn_factor * dist_factor
        self.cmd_v = max(0.3, self.cmd_v) if self.dist_to_goal > self.r_accept else 0.0

        # ================= 4-Thruster Motor Corrections =================
        # Maps (cmd_v, cmd_w) to the 4 BlueRobotics T200 thrusters to show active motor compensation
        f_surge = 25.0 * self.cmd_v
        tau_yaw = 18.0 * self.cmd_w
        t_port = 0.5 * f_surge - 0.25 * (tau_yaw / max(self.arm_y, 0.05))
        t_stbd = 0.5 * f_surge + 0.25 * (tau_yaw / max(self.arm_y, 0.05))
        t_bow  = +0.25 * (tau_yaw / max(self.arm_x_bow, 0.05))
        t_stern= -0.25 * (tau_yaw / max(self.arm_x_stern, 0.05))

        # Clamp and convert to microsecond PWMs (1100-1900us, 1500us neutral)
        pwm_m1 = int(np.clip(1500 + round(400.0 * (t_port / 60.0)), 1100, 1900))
        pwm_m2 = int(np.clip(1500 + round(400.0 * (t_stbd / 60.0)), 1100, 1900))
        pwm_m3 = int(np.clip(1500 + round(400.0 * (t_bow / 60.0)), 1100, 1900))
        pwm_m4 = int(np.clip(1500 + round(400.0 * (t_stern / 60.0)), 1100, 1900))
        self.motor_pwms = [pwm_m1, pwm_m2, pwm_m3, pwm_m4]

        # Publish Twist command to vessel
        cmd = Twist()
        cmd.linear.x = float(self.cmd_v)
        cmd.angular.z = float(self.cmd_w)
        self.cmd_pub.publish(cmd)

        # Publish 3D cross-track deviation marker line in RViz
        self.publish_cross_track_marker(proj_point)

        # Throttled console logger (every 1.0 s)
        now_sec = self.get_clock().now().nanoseconds * 1e-9
        if now_sec - self.last_log_time >= 1.0:
            self.last_log_time = now_sec
            side_str = "Babor (Port)" if self.cross_track_error > 0.05 else ("Estribor (Stbd)" if self.cross_track_error < -0.05 else "Centrado")
            wp_total = len(self.waypoint_queue)
            wp_cur = self.current_wp_idx + 1
            cur_name = self.waypoint_names[self.current_wp_idx] if self.current_wp_idx < len(self.waypoint_names) else ""
            self.get_logger().info(
                f"[LOS NAV] WP {wp_cur}/{wp_total} ({cur_name}) | Dist: {self.dist_to_goal:.1f}m "
                f"| Desviación e: {abs(self.cross_track_error):.2f}m [{side_str}] | Err Rumbo: {math.degrees(self.heading_error):+.1f}° "
                f"| Motores: M1(Port)={pwm_m1}us, M2(Stbd)={pwm_m2}us, M3(Bow)={pwm_m3}us, M4(Stern)={pwm_m4}us"
            )

    def stop_vessel(self):
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_pub.publish(cmd)
        self.motor_pwms = [1500, 1500, 1500, 1500]

    def publish_telemetry(self):
        # 1. Cross-Track Error
        e_msg = Float32()
        e_msg.data = float(self.cross_track_error)
        self.cross_track_pub.publish(e_msg)

        # 2. Status string
        s_msg = String()
        wp_str = f"WP {self.current_wp_idx+1}/{len(self.waypoint_queue)}" if self.active_goal is not None else ""
        s_msg.data = f"{self.status} {wp_str} | Err: {self.cross_track_error:+.2f}m | Dist: {self.dist_to_goal:.1f}m"
        self.status_pub.publish(s_msg)

        # 3. Telemetry MultiArray for Dashboard
        # [e_cross, heading_err_deg, dist_to_goal, current_wp_idx+1, total_wps, cmd_v, cmd_w, M1, M2, M3, M4]
        telem_msg = Float32MultiArray()
        telem_msg.data = [
            float(self.cross_track_error),
            float(math.degrees(self.heading_error)),
            float(self.dist_to_goal),
            float(self.current_wp_idx + 1),
            float(len(self.waypoint_queue)),
            float(self.cmd_v),
            float(self.cmd_w),
            float(self.motor_pwms[0]),
            float(self.motor_pwms[1]),
            float(self.motor_pwms[2]),
            float(self.motor_pwms[3])
        ]
        self.telemetry_pub.publish(telem_msg)

        # 4. Actual Path (breadcrumbs)
        if self.status == "NAVIGATING":
            self.publish_actual_path()

    def publish_planned_path(self):
        path_msg = Path()
        path_msg.header.frame_id = 'odom'
        path_msg.header.stamp = self.get_clock().now().to_msg()

        if self.segment_start_pos is not None:
            p0 = PoseStamped()
            p0.header = path_msg.header
            p0.pose.position.x = float(self.segment_start_pos[0])
            p0.pose.position.y = float(self.segment_start_pos[1])
            path_msg.poses.append(p0)

        for wp in self.waypoint_queue:
            p = PoseStamped()
            p.header = path_msg.header
            p.pose.position.x = float(wp[0])
            p.pose.position.y = float(wp[1])
            path_msg.poses.append(p)

        self.planned_path_pub.publish(path_msg)

    def publish_actual_path(self):
        path_msg = Path()
        path_msg.header.frame_id = 'odom'
        path_msg.header.stamp = self.get_clock().now().to_msg()

        for pt in self.actual_path_history:
            p = PoseStamped()
            p.header = path_msg.header
            p.pose.position.x = float(pt[0])
            p.pose.position.y = float(pt[1])
            path_msg.poses.append(p)

        self.actual_path_pub.publish(path_msg)

    def publish_cross_track_marker(self, proj_point):
        """Draws a red line from vessel position to closest point on target trajectory."""
        m = Marker()
        m.header.frame_id = 'odom'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'cross_track_deviation'
        m.id = 999
        m.type = Marker.LINE_STRIP
        m.action = Marker.ADD
        m.scale.x = 0.08  # Line width
        m.color.r = 1.0; m.color.g = 0.1; m.color.b = 0.2; m.color.a = 0.9

        p1 = Point()
        p1.x = float(self.pos[0]); p1.y = float(self.pos[1]); p1.z = 0.1
        p2 = Point()
        p2.x = float(proj_point[0]); p2.y = float(proj_point[1]); p2.z = 0.1

        m.points = [p1, p2]
        self.cross_track_marker_pub.publish(m)

    def publish_markers(self):
        marker_array = MarkerArray()

        del_marker = Marker()
        del_marker.action = Marker.DELETEALL
        marker_array.markers.append(del_marker)

        for i, wp in enumerate(self.waypoint_queue):
            # Cylinder marker
            m = Marker()
            m.header.frame_id = 'odom'
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = 'waypoints'
            m.id = i + 1
            m.type = Marker.CYLINDER
            m.action = Marker.ADD
            m.pose.position.x = float(wp[0])
            m.pose.position.y = float(wp[1])
            m.pose.position.z = 0.15
            m.scale.x = float(self.r_accept * 2.0)
            m.scale.y = float(self.r_accept * 2.0)
            m.scale.z = 0.12

            if i == self.current_wp_idx and self.active_goal is not None:
                # Active target: Bright lime green
                m.color.r = 0.0; m.color.g = 1.0; m.color.b = 0.3; m.color.a = 0.6
            elif i < self.current_wp_idx:
                # Completed: Muted grey
                m.color.r = 0.5; m.color.g = 0.5; m.color.b = 0.5; m.color.a = 0.3
            else:
                # Upcoming: Cyan/Blue
                m.color.r = 0.0; m.color.g = 0.7; m.color.b = 1.0; m.color.a = 0.4

            marker_array.markers.append(m)

            # Text label above waypoint
            t = Marker()
            t.header.frame_id = 'odom'
            t.header.stamp = self.get_clock().now().to_msg()
            t.ns = 'wp_labels'
            t.id = 1000 + i
            t.type = Marker.TEXT_VIEW_FACING
            t.action = Marker.ADD
            t.pose.position.x = float(wp[0])
            t.pose.position.y = float(wp[1])
            t.pose.position.z = 0.9
            t.scale.z = 0.5  # Text height
            t.color.r = 1.0; t.color.g = 1.0; t.color.b = 1.0; t.color.a = 0.95
            label = self.waypoint_names[i] if i < len(self.waypoint_names) else f"WP {i+1}"
            t.text = f"{i+1}: {label}"
            marker_array.markers.append(t)

        self.markers_pub.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavigatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_vessel()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
