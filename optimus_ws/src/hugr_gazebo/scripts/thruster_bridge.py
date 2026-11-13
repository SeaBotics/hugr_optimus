#!/usr/bin/env python3
"""
Hugr Optimus - Gazebo Thruster Bridge Node
Bridges standard ROS 2 topics (/motor_pwms and /cmd_vel) into Gazebo's
individual thruster topics (/hugr/thrusters/m[1-4]/cmd_thrust).

This allows:
1. Keyboard teleoperation (teleop_twist_keyboard -> /cmd_vel)
2. Gamepad joystick (thrust_allocation -> /motor_pwms)
3. Automated motor test scripts (test_motors.py -> /motor_pwms)
4. Web motor dashboard (motor_dashboard.py -> /motor_pwms)
5. Autonomous waypoint navigation (hugr_autonomy -> /cmd_vel)
to immediately drive the boat in Gazebo without manual translation.
"""

import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Int32MultiArray
from geometry_msgs.msg import Twist

class GazeboThrusterBridge(Node):
    def __init__(self):
        super().__init__('gazebo_thruster_bridge')

        # Parameters
        self.declare_parameter('max_thrust_n', 40.0)
        self.declare_parameter('arm_y', 0.1518)
        self.declare_parameter('arm_x_bow', 0.2884)
        self.declare_parameter('arm_x_stern', 0.4066)

        self.max_thrust = float(self.get_parameter('max_thrust_n').value)
        self.arm_y = float(self.get_parameter('arm_y').value)
        self.arm_x_bow = float(self.get_parameter('arm_x_bow').value)
        self.arm_x_stern = float(self.get_parameter('arm_x_stern').value)

        # 4 Gazebo internal thruster command publishers (hidden from ros2 topic list)
        self.m1_pub = self.create_publisher(Float64, '/_hugr/thrusters/m1/cmd_thrust', 10)
        self.m2_pub = self.create_publisher(Float64, '/_hugr/thrusters/m2/cmd_thrust', 10)
        self.m3_pub = self.create_publisher(Float64, '/_hugr/thrusters/m3/cmd_thrust', 10)
        self.m4_pub = self.create_publisher(Float64, '/_hugr/thrusters/m4/cmd_thrust', 10)

        # Publisher for /motor_pwms (so monitoring tools see PWMs if driven by /cmd_vel)
        self.pwm_echo_pub = self.create_publisher(Int32MultiArray, '/motor_pwms', 10)

        # Subscriptions to standard ROS 2 control topics
        self.pwm_sub = self.create_subscription(
            Int32MultiArray, '/motor_pwms', self.on_motor_pwms, 10
        )
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.on_cmd_vel, 10
        )

        self.last_cmd_source = "none"
        self.last_log_time = 0.0

        self.get_logger().info(
            "Gazebo Thruster Bridge initialized.\n"
            "  -> Listening to: /motor_pwms (Int32MultiArray [1100..1900 us])\n"
            "  -> Listening to: /cmd_vel (Twist)\n"
            "  -> Publishing to: /hugr/thrusters/m[1-4]/cmd_thrust (Float64 [N])"
        )

    def send_thrusts(self, t1: float, t2: float, t3: float, t4: float, source: str):
        # Clip to motor physical limits
        t1 = max(-self.max_thrust, min(self.max_thrust, float(t1)))
        t2 = max(-self.max_thrust, min(self.max_thrust, float(t2)))
        t3 = max(-self.max_thrust, min(self.max_thrust, float(t3)))
        t4 = max(-self.max_thrust, min(self.max_thrust, float(t4)))

        self.m1_pub.publish(Float64(data=t1))
        self.m2_pub.publish(Float64(data=t2))
        self.m3_pub.publish(Float64(data=t3))
        self.m4_pub.publish(Float64(data=t4))

        # Throttled live console feedback (1 Hz when active)
        now = time.time()
        is_active = any(abs(t) > 0.5 for t in (t1, t2, t3, t4))
        if is_active and (now - self.last_log_time >= 1.0):
            self.last_log_time = now
            self.get_logger().info(
                f"[{source.upper()}] Thrust -> M1(Port)={t1:+.1f}N | M2(Stbd)={t2:+.1f}N | "
                f"M3(Bow)={t3:+.1f}N | M4(Stern)={t4:+.1f}N"
            )

    def on_motor_pwms(self, msg: Int32MultiArray):
        # Prevent feedback loop if we echoed it ourselves
        if self.last_cmd_source == "cmd_vel" and time.time() - self.last_log_time < 0.05:
            return

        if len(msg.data) < 4:
            return

        self.last_cmd_source = "pwms"

        # Convert PWM (1100..1900 us, 1500 neutral) to Thrust in Newtons
        t1 = ((float(msg.data[0]) - 1500.0) / 400.0) * self.max_thrust
        t2 = ((float(msg.data[1]) - 1500.0) / 400.0) * self.max_thrust
        t3 = ((float(msg.data[2]) - 1500.0) / 400.0) * self.max_thrust
        t4 = ((float(msg.data[3]) - 1500.0) / 400.0) * self.max_thrust

        self.send_thrusts(t1, t2, t3, t4, source="motor_pwms")

    def on_cmd_vel(self, msg: Twist):
        self.last_cmd_source = "cmd_vel"

        u = msg.linear.x        # Surge (m/s)
        v = msg.linear.y        # Sway (m/s)
        r = msg.angular.z       # Yaw (rad/s)

        # Proportional mapping calibrated to vessel hydrodynamic drag:
        f_surge = 25.0 * u
        f_sway = 35.0 * v
        tau_yaw = 18.0 * r

        # 4-Thruster Allocation
        # M1 (Port), M2 (Starboard): Longitudinal surge + differential yaw
        t_port = 0.5 * f_surge - 0.25 * (tau_yaw / max(self.arm_y, 0.05))
        t_stbd = 0.5 * f_surge + 0.25 * (tau_yaw / max(self.arm_y, 0.05))

        # M3 (Bow), M4 (Stern): Sway allocation weighted by moment arms
        sum_x = self.arm_x_bow + self.arm_x_stern
        ratio_bow = self.arm_x_stern / sum_x if sum_x > 0 else 0.5
        ratio_stern = self.arm_x_bow / sum_x if sum_x > 0 else 0.5
        t_bow = ratio_bow * f_sway + 0.25 * (tau_yaw / max(self.arm_x_bow, 0.05))
        t_stern = ratio_stern * f_sway - 0.25 * (tau_yaw / max(self.arm_x_stern, 0.05))

        self.send_thrusts(t_port, t_stbd, t_bow, t_stern, source="cmd_vel")

def main(args=None):
    rclpy.init(args=args)
    node = GazeboThrusterBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.send_thrusts(0, 0, 0, 0, source="shutdown")
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
