#!/usr/bin/env python3
"""
Fossen Marine Hydrodynamics Simulator for Hugr Optimus ASV
Based on Thor I. Fossen's "Handbook of Marine Craft Hydrodynamics and Motion Control"
Simulates 3-DOF horizontal maneuvering (Surge, Sway, Yaw) with added mass, 
hydrodynamic damping, and ocean currents.
"""

import math
import time
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped, PoseArray, Pose
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, NavSatFix
from std_msgs.msg import Int32MultiArray, Float32MultiArray
from visualization_msgs.msg import Marker, MarkerArray
from std_srvs.srv import Empty
import tf2_ros

class FossenSimNode(Node):
    def __init__(self):
        super().__init__('fossen_sim_node')

        # Declare parameters
        self.declare_parameter('sim.rate_hz', 50.0)
        self.declare_parameter('sim.fixed_frame', 'odom')
        self.declare_parameter('sim.base_frame', 'base_footprint')

        # Vessel parameters
        self.declare_parameter('vessel.mass', 28.0)
        self.declare_parameter('vessel.iz', 5.2)
        self.declare_parameter('vessel.xg', 0.0)
        self.declare_parameter('vessel.yg', 0.0)

        # Added mass
        self.declare_parameter('added_mass.X_u_dot', -3.5)
        self.declare_parameter('added_mass.Y_v_dot', -18.0)
        self.declare_parameter('added_mass.N_r_dot', -4.5)

        # Damping
        self.declare_parameter('damping.X_u', -14.0)
        self.declare_parameter('damping.Y_v', -35.0)
        self.declare_parameter('damping.N_r', -15.0)
        self.declare_parameter('damping.X_uu', -20.0)
        self.declare_parameter('damping.Y_vv', -65.0)
        self.declare_parameter('damping.N_rr', -25.0)

        # Thrusters (calibrated to exact OnShape CAD assembly model)
        self.declare_parameter('thrusters.arm_y', 0.1518)
        self.declare_parameter('thrusters.arm_x_bow', 0.2884)
        self.declare_parameter('thrusters.arm_x_stern', 0.4066)
        self.declare_parameter('thrusters.arm_x_main', 0.2323)
        self.declare_parameter('thrusters.max_thrust_per_motor', 60.0)
        self.declare_parameter('thrusters.time_constant', 0.12)

        # Environment: Ocean Surface Currents
        self.declare_parameter('environment.ocean_current_speed', 0.20)
        self.declare_parameter('environment.ocean_current_angle_deg', 45.0)
        self.declare_parameter('environment.enable_current', False)

        # Environment: Ocean Waves & Swell Dynamics (Gerstner Waves)
        self.declare_parameter('environment.waves.enable_waves', True)
        self.declare_parameter('environment.waves.significant_height', 0.12)
        self.declare_parameter('environment.waves.wave_length', 3.2)
        self.declare_parameter('environment.waves.wave_direction_deg', 40.0)
        self.declare_parameter('environment.waves.wave_drift_coeff', 0.20)

        # Environment: Marine Wind Drag
        self.declare_parameter('environment.wind.enable_wind', False)
        self.declare_parameter('environment.wind.wind_speed', 3.5)
        self.declare_parameter('environment.wind.wind_direction_deg', 90.0)

        # Competition: Buoy Channel Simulation
        self.declare_parameter('environment.competition.publish_buoys', True)
        self.declare_parameter('environment.competition.publish_rate_hz', 5.0)
        self.declare_parameter('environment.competition.max_detection_range', 20.0)
        self.declare_parameter('environment.competition.camera_fov_deg', 72.0)

        # GNSS Reference
        self.declare_parameter('gnss.origin_latitude', 58.334000)
        self.declare_parameter('gnss.origin_longitude', 8.578000)
        self.declare_parameter('gnss.origin_altitude', 0.0)

        # Fetch parameters
        self.rate_hz = self.get_parameter('sim.rate_hz').value
        self.dt = 1.0 / self.rate_hz
        self.fixed_frame = self.get_parameter('sim.fixed_frame').value
        self.base_frame = self.get_parameter('sim.base_frame').value

        self.m = self.get_parameter('vessel.mass').value
        self.iz = self.get_parameter('vessel.iz').value
        self.xg = self.get_parameter('vessel.xg').value
        self.yg = self.get_parameter('vessel.yg').value

        self.X_u_dot = self.get_parameter('added_mass.X_u_dot').value
        self.Y_v_dot = self.get_parameter('added_mass.Y_v_dot').value
        self.N_r_dot = self.get_parameter('added_mass.N_r_dot').value

        self.X_u = self.get_parameter('damping.X_u').value
        self.Y_v = self.get_parameter('damping.Y_v').value
        self.N_r = self.get_parameter('damping.N_r').value
        self.X_uu = self.get_parameter('damping.X_uu').value
        self.Y_vv = self.get_parameter('damping.Y_vv').value
        self.N_rr = self.get_parameter('damping.N_rr').value

        self.arm_y = self.get_parameter('thrusters.arm_y').value
        self.arm_x_bow = self.get_parameter('thrusters.arm_x_bow').value
        self.arm_x_stern = self.get_parameter('thrusters.arm_x_stern').value
        self.arm_x_main = self.get_parameter('thrusters.arm_x_main').value
        self.max_thrust = self.get_parameter('thrusters.max_thrust_per_motor').value
        self.tau_motor = self.get_parameter('thrusters.time_constant').value

        self.lat_origin = self.get_parameter('gnss.origin_latitude').value
        self.lon_origin = self.get_parameter('gnss.origin_longitude').value
        self.alt_origin = self.get_parameter('gnss.origin_altitude').value

        # Fetch Environment properties
        self.enable_waves = bool(self.get_parameter('environment.waves.enable_waves').value)
        self.wave_hs = float(self.get_parameter('environment.waves.significant_height').value)
        self.wave_len = float(self.get_parameter('environment.waves.wave_length').value)
        self.wave_dir = math.radians(float(self.get_parameter('environment.waves.wave_direction_deg').value))
        self.wave_drift_c = float(self.get_parameter('environment.waves.wave_drift_coeff').value)

        self.enable_wind = bool(self.get_parameter('environment.wind.enable_wind').value)
        self.wind_speed = float(self.get_parameter('environment.wind.wind_speed').value)
        self.wind_dir = math.radians(float(self.get_parameter('environment.wind.wind_direction_deg').value))

        self.publish_buoys = bool(self.get_parameter('environment.competition.publish_buoys').value)
        self.buoy_range = float(self.get_parameter('environment.competition.max_detection_range').value)
        self.buoy_fov = math.radians(float(self.get_parameter('environment.competition.camera_fov_deg').value))

        # Wave dispersion physics: k = 2*pi / lambda, omega = sqrt(g * k)
        g = 9.81
        self.wave_k = 2.0 * math.pi / max(self.wave_len, 0.5)
        self.wave_omega = math.sqrt(g * self.wave_k)
        self.wave_amp = self.wave_hs * 0.5

        # 6-DOF Wave induced kinematic states
        self.z_heave = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.roll_rate = 0.0
        self.pitch_rate = 0.0
        self.heave_accel = 0.0

        # Competition buoys field definition (East [m], North [m], Color, Radius [m])
        self.competition_buoys = [
            {"id": 1, "x": 8.0, "y": 2.0, "color": "red", "radius": 0.25},
            {"id": 2, "x": 8.0, "y": -2.0, "color": "green", "radius": 0.25},
            {"id": 3, "x": 18.0, "y": 3.0, "color": "red", "radius": 0.25},
            {"id": 4, "x": 18.0, "y": -1.0, "color": "green", "radius": 0.25},
            {"id": 5, "x": 28.0, "y": 0.0, "color": "yellow", "radius": 0.35},
        ]
        self.last_buoy_pub_time = 0.0

        # Build Mass Matrix M = M_RB + M_A
        self.m11 = self.m - self.X_u_dot
        self.m22 = self.m - self.Y_v_dot
        self.m33 = self.iz - self.N_r_dot
        self.M = np.array([
            [self.m11, 0.0, -self.m * self.yg],
            [0.0, self.m22, self.m * self.xg],
            [-self.m * self.yg, self.m * self.xg, self.m33]
        ], dtype=float)
        self.M_inv = np.linalg.inv(self.M)

        # State Variables
        # eta = [x (East), y (North), psi (Heading rad CCW from East in ROS ENU)]
        self.eta = np.zeros(3, dtype=float)
        # nu = [u (surge m/s), v (sway m/s), r (yaw rate rad/s)]
        self.nu = np.zeros(3, dtype=float)
        # Accelerations
        self.nu_dot = np.zeros(3, dtype=float)

        # Actual Thruster forces [M1: Port, M2: Starboard, M3: Bow Transverse, M4: Stern Transverse]
        self.thrust_actual = np.zeros(4, dtype=float)
        # Commanded Thruster forces
        self.thrust_cmd = np.zeros(4, dtype=float)

        # ROS 2 Subscriptions & Publishers
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.motor_pwms_sub = self.create_subscription(Int32MultiArray, '/motor_pwms', self.motor_pwms_callback, 10)
        self.thrust_pub = self.create_publisher(Float32MultiArray, '/thrusters/actual_thrust', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odometry', 10)
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.gnss_pub = self.create_publisher(NavSatFix, '/gnss/fix', 10)
        self.wave_telemetry_pub = self.create_publisher(Float32MultiArray, '/environment/wave_telemetry', 10)
        self.buoy_markers_pub = self.create_publisher(MarkerArray, '/competition/buoy_markers', 10)
        self.detected_buoys_pub = self.create_publisher(PoseArray, '/competition/detected_buoys', 10)

        # TF Broadcaster
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Reset service
        self.reset_srv = self.create_service(Empty, '/hugr_sim/reset', self.reset_callback)

        # Main simulation timer
        self.timer = self.create_timer(self.dt, self.sim_step)

        self.get_logger().info('Fossen Marine Hydrodynamics & Gerstner Wave Simulator started at %.1f Hz' % self.rate_hz)
        self.get_logger().info('Sea State: Waves=%s (Hs=%.2fm, L=%.1fm, Dir=%.0f°)' % 
                               (self.enable_waves, self.wave_hs, self.wave_len, math.degrees(self.wave_dir)))
        self.get_logger().info('Vessel 4-Thruster Layout: Port, Starboard, Bow Transverse, Stern Transverse (Max 4x%.1fN)' % self.max_thrust)

    def reset_callback(self, request, response):
        self.eta = np.zeros(3, dtype=float)
        self.nu = np.zeros(3, dtype=float)
        self.nu_dot = np.zeros(3, dtype=float)
        self.thrust_actual = np.zeros(4, dtype=float)
        self.thrust_cmd = np.zeros(4, dtype=float)
        self.get_logger().info('Simulation state reset to origin.')
        return response

    def cmd_vel_callback(self, msg: Twist):
        """
        Translates Twist (/cmd_vel) to 4-thruster commands:
        linear.x (m/s)  -> Forward surge thrust (M1 Port, M2 Starboard)
        linear.y (m/s)  -> Lateral sway thrust (M3 Bow, M4 Stern)
        angular.z (rad/s) -> Yaw torque (M1/M2 differential + M3/M4 opposing)
        """
        v_target = msg.linear.x
        v_sway_target = msg.linear.y
        w_target = msg.angular.z

        # Proportional mapping calibrated to steady-state hydrodynamic drag:
        f_surge = 25.0 * v_target
        f_sway = 35.0 * v_sway_target
        tau_yaw = 18.0 * w_target

        # 4-Thruster Allocation calibrated to CAD moment arms:
        # M1 (Port), M2 (Starboard): Longitudinal surge + differential yaw
        t_port = 0.5 * f_surge - 0.25 * (tau_yaw / max(self.arm_y, 0.05))
        t_stbd = 0.5 * f_surge + 0.25 * (tau_yaw / max(self.arm_y, 0.05))

        # M3 (Bow), M4 (Stern): Sway allocation weighted by moment arms to ensure pure lateral strafe (zero induced yaw)
        # Ratio ensures: T_bow * x_bow == T_stern * x_stern during pure sway
        sum_x = self.arm_x_bow + self.arm_x_stern
        ratio_bow = self.arm_x_stern / sum_x if sum_x > 0 else 0.5
        ratio_stern = self.arm_x_bow / sum_x if sum_x > 0 else 0.5
        t_bow = ratio_bow * f_sway + 0.25 * (tau_yaw / max(self.arm_x_bow, 0.05))
        t_stern = ratio_stern * f_sway - 0.25 * (tau_yaw / max(self.arm_x_stern, 0.05))

        # Clamp thruster output to motor limits
        self.thrust_cmd[0] = np.clip(t_port, -self.max_thrust, self.max_thrust)
        self.thrust_cmd[1] = np.clip(t_stbd, -self.max_thrust, self.max_thrust)
        self.thrust_cmd[2] = np.clip(t_bow, -self.max_thrust, self.max_thrust)
        self.thrust_cmd[3] = np.clip(t_stern, -self.max_thrust, self.max_thrust)

    def motor_pwms_callback(self, msg: Int32MultiArray):
        """
        Receives PWM signals directly matching the ESP32 micro-ROS firmware:
        msg.data = [PWM_port, PWM_starboard, PWM_bow, PWM_stern] in microseconds (1100 to 1900 us, 1500 us neutral).
        Converts PWM directly into thruster force (Newtons) in the physics simulator.
        """
        if len(msg.data) >= 4:
            for i in range(4):
                norm = np.clip((float(msg.data[i]) - 1500.0) / 400.0, -1.0, 1.0)
                self.thrust_cmd[i] = norm * self.max_thrust
        elif len(msg.data) >= 2:
            norm_port = np.clip((float(msg.data[0]) - 1500.0) / 400.0, -1.0, 1.0)
            norm_stbd = np.clip((float(msg.data[1]) - 1500.0) / 400.0, -1.0, 1.0)
            self.thrust_cmd[0] = norm_port * self.max_thrust
            self.thrust_cmd[1] = norm_stbd * self.max_thrust
            self.thrust_cmd[2] = 0.0
            self.thrust_cmd[3] = 0.0

        # Live feedback logging to console
        now_sec = self.get_clock().now().nanoseconds * 1e-9
        if not hasattr(self, '_last_log_pwm'):
            self._last_log_pwm = 0.0
        if not hasattr(self, '_was_active'):
            self._was_active = False

        is_active = any(abs(c) > 0.5 for c in self.thrust_cmd)
        if is_active:
            if not self._was_active:
                self.get_logger().info(f"[SIMULATOR] Motors ACTIVE: M1={msg.data[0]}us, M2={msg.data[1]}us, M3={msg.data[2]}us, M4={msg.data[3]}us")
                self._was_active = True
            if now_sec - self._last_log_pwm >= 1.0:
                self._last_log_pwm = now_sec
                pwms_str = f"M1(Port)={msg.data[0]}us, M2(Stbd)={msg.data[1]}us, M3(Bow)={msg.data[2]}us, M4(Stern)={msg.data[3]}us"
                forces_str = f"T1={self.thrust_actual[0]:+.1f}N, T2={self.thrust_actual[1]:+.1f}N, T3={self.thrust_actual[2]:+.1f}N, T4={self.thrust_actual[3]:+.1f}N"
                heading_deg = math.degrees(self.eta[2]) % 360.0
                self.get_logger().info(
                    f"[SIMULATOR RECV] PWMs: [{pwms_str}] | Thrust: [{forces_str}] | Velocity: surge={self.nu[0]:.2f}m/s, sway={self.nu[1]:.2f}m/s, yaw_rate={math.degrees(self.nu[2]):.1f}deg/s | Pos: X={self.eta[0]:.2f}m, Y={self.eta[1]:.2f}m, Heading={heading_deg:.1f}deg"
                )
        else:
            if self._was_active:
                self.get_logger().info("[SIMULATOR] Motors returned to NEUTRAL (1500us). Vessel decelerating to stop.")
                self._was_active = False

    def compute_dynamics(self, nu_val, psi_val, tau_applied):
        """
        Computes nu_dot = M_inv * (tau - C(nu_r)*nu_r - D(nu_r)*nu_r)
        """
        # Ocean current
        v_c = self.get_parameter('environment.ocean_current_speed').value
        beta_c = math.radians(self.get_parameter('environment.ocean_current_angle_deg').value)
        enable_curr = self.get_parameter('environment.enable_current').value

        if enable_curr and v_c > 0.0:
            u_c = v_c * math.cos(beta_c - psi_val)
            v_c_flow = v_c * math.sin(beta_c - psi_val)
        else:
            u_c = 0.0
            v_c_flow = 0.0

        # Relative velocity
        u_r = nu_val[0] - u_c
        v_r = nu_val[1] - v_c_flow
        r_r = nu_val[2]

        nu_r = np.array([u_r, v_r, r_r], dtype=float)

        # Coriolis matrix C(nu_r)
        c13 = -self.m22 * v_r - self.m * self.xg * r_r
        c23 = self.m11 * u_r - self.m * self.yg * r_r
        C = np.array([
            [0.0, 0.0, c13],
            [0.0, 0.0, c23],
            [-c13, -c23, 0.0]
        ], dtype=float)

        # Damping matrix D(nu_r)
        d11 = -(self.X_u + self.X_uu * abs(u_r))
        d22 = -(self.Y_v + self.Y_vv * abs(v_r))
        d33 = -(self.N_r + self.N_rr * abs(r_r))
        D = np.array([
            [d11, 0.0, 0.0],
            [0.0, d22, 0.0],
            [0.0, 0.0, d33]
        ], dtype=float)

        coriolis_force = C @ nu_r
        damping_force = D @ nu_r

        # Total generalized force: tau - C*nu_r - D*nu_r
        net_force = tau_applied - coriolis_force - damping_force

        nu_dot = self.M_inv @ net_force
        return nu_dot

    def calculate_wave_effects(self, t_sec):
        """
        Calculates Gerstner wave kinematics and 1st/2nd order hydrodynamic forces:
        Returns: (tau_waves, z_heave, roll, pitch, roll_rate, pitch_rate, heave_accel)
        """
        if not self.enable_waves or self.wave_amp < 0.001:
            return np.zeros(3, dtype=float), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        x = self.eta[0]
        y = self.eta[1]
        psi = self.eta[2]
        u = self.nu[0]
        v = self.nu[1]

        # Wave spatial phase: theta_w = omega * t - k * (x * cos(psi_w) + y * sin(psi_w))
        kx_ky = self.wave_k * (x * math.cos(self.wave_dir) + y * math.sin(self.wave_dir))
        theta_w = self.wave_omega * t_sec - kx_ky

        # Relative encounter angle (vessel heading relative to wave propagation direction)
        chi = psi - self.wave_dir

        # Doppler encounter frequency omega_e
        v_along_wave = u * math.cos(chi) - v * math.sin(chi)
        omega_e = max(0.1, abs(self.wave_omega - self.wave_k * v_along_wave))

        # 1. Heave: surface elevation at vessel CG
        z_heave = self.wave_amp * math.cos(theta_w)
        heave_accel = -self.wave_amp * (omega_e ** 2) * math.cos(theta_w)

        # 2. Pitch: longitudinal wave slope along vessel X-axis (bow-stern)
        pitch = -self.wave_amp * self.wave_k * math.cos(chi) * math.sin(theta_w)
        pitch_rate = -self.wave_amp * self.wave_k * omega_e * math.cos(chi) * math.cos(theta_w)

        # 3. Roll: transversal wave slope across catamaran pontoons (port-stbd)
        roll = self.wave_amp * self.wave_k * math.sin(chi) * math.sin(theta_w)
        roll_rate = self.wave_amp * self.wave_k * omega_e * math.sin(chi) * math.cos(theta_w)

        # 4. Hydrodynamic Forces & Moments on Fossen Equations:
        # F_wave = F_1st_order (oscillating) + F_2nd_order (mean drift)
        rho = 1025.0
        g = 9.81
        beam = 0.69
        length = 1.00
        draft = 0.08

        # 1st order oscillating wave excitation (Newtons / N*m)
        f_surge_1st = rho * g * self.wave_amp * beam * draft * self.wave_k * math.cos(chi) * math.cos(theta_w)
        f_sway_1st = rho * g * self.wave_amp * length * draft * self.wave_k * math.sin(chi) * math.cos(theta_w)
        tau_yaw_1st = (1.0 / 12.0) * rho * g * self.wave_amp * (length ** 2) * draft * self.wave_k * math.sin(2.0 * chi) * math.sin(theta_w)

        # 2nd order steady wave drift force (pushes vessel downwave)
        f_drift_mag = 0.5 * rho * g * (self.wave_amp ** 2) * beam * self.wave_drift_c
        f_surge_drift = f_drift_mag * math.cos(chi)
        f_sway_drift = -f_drift_mag * math.sin(chi)

        tau_waves = np.array([
            f_surge_1st + f_surge_drift,
            f_sway_1st + f_sway_drift,
            tau_yaw_1st
        ], dtype=float)

        return tau_waves, z_heave, roll, pitch, roll_rate, pitch_rate, heave_accel

    def calculate_wind_forces(self):
        """Calculates aerodynamic wind drag on the hull and electronics superstructure."""
        if not self.enable_wind or self.wind_speed <= 0.0:
            return np.zeros(3, dtype=float)

        chi_wind = self.eta[2] - self.wind_dir
        u = self.nu[0]
        v = self.nu[1]

        v_wx = self.wind_speed * math.cos(chi_wind) - u
        v_wy = -self.wind_speed * math.sin(chi_wind) - v

        rho_air = 1.225
        a_front = 0.15
        a_side = 0.35
        cx = 0.8
        cy = 1.1
        cn = 0.15

        f_wind_surge = 0.5 * rho_air * a_front * cx * v_wx * abs(v_wx)
        f_wind_sway = 0.5 * rho_air * a_side * cy * v_wy * abs(v_wy)
        tau_wind_yaw = 0.5 * rho_air * a_side * 1.0 * cn * v_wy * abs(v_wy)

        return np.array([f_wind_surge, f_wind_sway, tau_wind_yaw], dtype=float)

    @staticmethod
    def euler_to_quaternion(roll, pitch, yaw):
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)

        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy
        return qx, qy, qz, qw

    def sim_step(self):
        # 1. Update Thruster Lag: dT = (T_cmd - T) / tau_motor * dt
        alpha = self.dt / max(self.tau_motor, 0.01)
        self.thrust_actual += alpha * (self.thrust_cmd - self.thrust_actual)

        # 2. Compute Generalized Propulsion Forces (tau_prop)
        tau_u = self.thrust_actual[0] + self.thrust_actual[1]
        tau_v = self.thrust_actual[2] + self.thrust_actual[3]
        tau_r = (
            (self.thrust_actual[1] - self.thrust_actual[0]) * self.arm_y +
            self.thrust_actual[2] * self.arm_x_bow -
            self.thrust_actual[3] * self.arm_x_stern
        )
        tau_prop = np.array([tau_u, tau_v, tau_r], dtype=float)

        # 3. Calculate Ocean Waves & Wind Forces
        t_now = self.get_clock().now().nanoseconds * 1e-9
        tau_waves, z_heave, roll, pitch, roll_rate, pitch_rate, heave_accel = self.calculate_wave_effects(t_now)
        tau_wind = self.calculate_wind_forces()

        self.z_heave = z_heave
        self.roll = roll
        self.pitch = pitch
        self.roll_rate = roll_rate
        self.pitch_rate = pitch_rate
        self.heave_accel = heave_accel

        # Net external force on vessel: Propulsion + Waves + Wind
        tau_total = tau_prop + tau_waves + tau_wind

        # 4. Integrate Dynamics using Runge-Kutta 4 (RK4)
        k1_v = self.compute_dynamics(self.nu, self.eta[2], tau_total)
        k2_v = self.compute_dynamics(self.nu + 0.5 * self.dt * k1_v, self.eta[2], tau_total)
        k3_v = self.compute_dynamics(self.nu + 0.5 * self.dt * k2_v, self.eta[2], tau_total)
        k4_v = self.compute_dynamics(self.nu + self.dt * k3_v, self.eta[2], tau_total)

        self.nu_dot = (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v) / 6.0
        self.nu += self.nu_dot * self.dt

        # 5. Integrate Kinematics: eta_dot = J(psi) * nu
        psi = self.eta[2]
        c_psi = math.cos(psi)
        s_psi = math.sin(psi)

        x_dot = self.nu[0] * c_psi - self.nu[1] * s_psi
        y_dot = self.nu[0] * s_psi + self.nu[1] * c_psi
        psi_dot = self.nu[2]

        self.eta[0] += x_dot * self.dt
        self.eta[1] += y_dot * self.dt
        self.eta[2] += psi_dot * self.dt

        # Normalize yaw angle to [-pi, pi]
        self.eta[2] = math.atan2(math.sin(self.eta[2]), math.cos(self.eta[2]))

        # 6. Publish ROS 2 Messages, 6-DOF TF, Waves, and Competition Buoys
        now = self.get_clock().now().to_msg()
        self.publish_tf(now)
        self.publish_odometry(now)
        self.publish_imu(now)
        self.publish_gnss(now)
        self.publish_thrust()
        self.publish_wave_telemetry()
        self.publish_competition_buoys(now)

    def publish_tf(self, timestamp):
        t = TransformStamped()
        t.header.stamp = timestamp
        t.header.frame_id = self.fixed_frame
        t.child_frame_id = self.base_frame

        t.transform.translation.x = float(self.eta[0])
        t.transform.translation.y = float(self.eta[1])
        t.transform.translation.z = float(self.z_heave)

        qx, qy, qz, qw = self.euler_to_quaternion(self.roll, self.pitch, self.eta[2])
        t.transform.rotation.x = float(qx)
        t.transform.rotation.y = float(qy)
        t.transform.rotation.z = float(qz)
        t.transform.rotation.w = float(qw)

        self.tf_broadcaster.sendTransform(t)

    def publish_odometry(self, timestamp):
        msg = Odometry()
        msg.header.stamp = timestamp
        msg.header.frame_id = self.fixed_frame
        msg.child_frame_id = self.base_frame

        msg.pose.pose.position.x = float(self.eta[0])
        msg.pose.pose.position.y = float(self.eta[1])
        msg.pose.pose.position.z = float(self.z_heave)

        qx, qy, qz, qw = self.euler_to_quaternion(self.roll, self.pitch, self.eta[2])
        msg.pose.pose.orientation.x = float(qx)
        msg.pose.pose.orientation.y = float(qy)
        msg.pose.pose.orientation.z = float(qz)
        msg.pose.pose.orientation.w = float(qw)

        # Covariance
        msg.pose.covariance[0] = 0.01
        msg.pose.covariance[7] = 0.01
        msg.pose.covariance[14] = 0.01
        msg.pose.covariance[21] = 0.005
        msg.pose.covariance[28] = 0.005
        msg.pose.covariance[35] = 0.01

        # Twist in body frame (Linear + 3D Angular Velocity)
        msg.twist.twist.linear.x = float(self.nu[0])
        msg.twist.twist.linear.y = float(self.nu[1])
        msg.twist.twist.linear.z = float(-self.heave_accel * self.dt)
        msg.twist.twist.angular.x = float(self.roll_rate)
        msg.twist.twist.angular.y = float(self.pitch_rate)
        msg.twist.twist.angular.z = float(self.nu[2])

        self.odom_pub.publish(msg)

    def publish_imu(self, timestamp):
        msg = Imu()
        msg.header.stamp = timestamp
        msg.header.frame_id = 'imu_link'

        qx, qy, qz, qw = self.euler_to_quaternion(self.roll, self.pitch, self.eta[2])
        msg.orientation.x = float(qx)
        msg.orientation.y = float(qy)
        msg.orientation.z = float(qz)
        msg.orientation.w = float(qw)

        msg.angular_velocity.x = float(self.roll_rate)
        msg.angular_velocity.y = float(self.pitch_rate)
        msg.angular_velocity.z = float(self.nu[2])

        # Accelerometer measuring linear acceleration + gravity vector projected onto rotated frame
        g = 9.81
        msg.linear_acceleration.x = float(self.nu_dot[0] - self.nu[2] * self.nu[1] + g * math.sin(self.pitch))
        msg.linear_acceleration.y = float(self.nu_dot[1] + self.nu[2] * self.nu[0] - g * math.sin(self.roll) * math.cos(self.pitch))
        msg.linear_acceleration.z = float(g * math.cos(self.roll) * math.cos(self.pitch) + self.heave_accel)

        self.imu_pub.publish(msg)

    def publish_gnss(self, timestamp):
        msg = NavSatFix()
        msg.header.stamp = timestamp
        msg.header.frame_id = 'base_link'

        # Spherical projection from local (x, y) meters to lat/lon
        r_earth = 6378137.0
        d_lat = (self.eta[1] / r_earth) * (180.0 / math.pi)
        d_lon = (self.eta[0] / (r_earth * math.cos(math.radians(self.lat_origin)))) * (180.0 / math.pi)

        msg.latitude = float(self.lat_origin + d_lat)
        msg.longitude = float(self.lon_origin + d_lon)
        msg.altitude = float(self.alt_origin + self.z_heave)

        msg.status.status = 0  # STATUS_FIX
        msg.position_covariance[0] = 0.25
        msg.position_covariance[4] = 0.25
        msg.position_covariance[8] = 0.5

        self.gnss_pub.publish(msg)

    def publish_thrust(self):
        msg = Float32MultiArray()
        msg.data = [float(t) for t in self.thrust_actual]
        self.thrust_pub.publish(msg)

    def publish_wave_telemetry(self):
        msg = Float32MultiArray()
        # [wave_hs, wave_len, wave_dir_deg, z_heave, roll_deg, pitch_deg]
        msg.data = [
            float(self.wave_hs),
            float(self.wave_len),
            float(math.degrees(self.wave_dir)),
            float(self.z_heave),
            float(math.degrees(self.roll)),
            float(math.degrees(self.pitch))
        ]
        self.wave_telemetry_pub.publish(msg)

    def publish_competition_buoys(self, timestamp):
        if not self.publish_buoys:
            return

        now_sec = self.get_clock().now().nanoseconds * 1e-9
        rate = max(1.0, float(self.get_parameter('environment.competition.publish_rate_hz').value))
        if now_sec - self.last_buoy_pub_time < (1.0 / rate):
            return
        self.last_buoy_pub_time = now_sec

        # 1. Publish 3D Colored Markers for RViz
        marker_array = MarkerArray()
        for b in self.competition_buoys:
            m = Marker()
            m.header.stamp = timestamp
            m.header.frame_id = self.fixed_frame
            m.ns = "competition_buoys"
            m.id = int(b["id"])
            m.type = Marker.CYLINDER
            m.action = Marker.ADD
            m.pose.position.x = float(b["x"])
            m.pose.position.y = float(b["y"])
            # Buoy bobs slightly on water
            m.pose.position.z = 0.25
            m.pose.orientation.w = 1.0
            m.scale.x = float(b["radius"] * 2.0)
            m.scale.y = float(b["radius"] * 2.0)
            m.scale.z = 0.70

            if b["color"] == "red":
                m.color.r = 1.0; m.color.g = 0.1; m.color.b = 0.1; m.color.a = 0.95
            elif b["color"] == "green":
                m.color.r = 0.1; m.color.g = 1.0; m.color.b = 0.2; m.color.a = 0.95
            else:  # yellow
                m.color.r = 1.0; m.color.g = 0.9; m.color.b = 0.0; m.color.a = 0.95

            marker_array.markers.append(m)

        self.buoy_markers_pub.publish(marker_array)

        # 2. Publish Simulated Detected Buoys within Camera FOV (base_link frame)
        detected_poses = PoseArray()
        detected_poses.header.stamp = timestamp
        detected_poses.header.frame_id = 'base_link'

        v_x = self.eta[0]
        v_y = self.eta[1]
        psi = self.eta[2]

        for b in self.competition_buoys:
            dx = b["x"] - v_x
            dy = b["y"] - v_y
            dist = math.hypot(dx, dy)
            if dist <= self.buoy_range:
                # Bearing from vessel heading
                bearing = math.atan2(dy, dx)
                rel_bearing = math.atan2(math.sin(bearing - psi), math.cos(bearing - psi))
                if abs(rel_bearing) <= (self.buoy_fov * 0.5):
                    p = Pose()
                    # Relative coordinates in vessel body frame (+X forward, +Y port)
                    p.position.x = dist * math.cos(rel_bearing)
                    p.position.y = dist * math.sin(rel_bearing)
                    p.position.z = 0.0
                    p.orientation.z = float(rel_bearing)
                    p.orientation.w = 1.0
                    detected_poses.poses.append(p)

        self.detected_buoys_pub.publish(detected_poses)

def main(args=None):
    rclpy.init(args=args)
    node = FossenSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
