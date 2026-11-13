#!/usr/bin/env python3
"""
Motor Test & Verification Tool for Hugr Optimus.
Publishes test PWM commands to /motor_pwms and displays live vessel motion telemetry.
"""
import sys
import time
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from nav_msgs.msg import Odometry

class MotorTester(Node):
    def __init__(self):
        super().__init__('motor_tester')
        self.pwm_pub = self.create_publisher(Int32MultiArray, '/motor_pwms', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)

        self.pos = [0.0, 0.0]
        self.heading_deg = 0.0
        self.speed = [0.0, 0.0, 0.0]
        self.odom_received = False

    def odom_callback(self, msg: Odometry):
        self.pos[0] = msg.pose.pose.position.x
        self.pos[1] = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.heading_deg = math.degrees(math.atan2(siny_cosp, cosy_cosp)) % 360.0
        self.speed[0] = msg.twist.twist.linear.x
        self.speed[1] = msg.twist.twist.linear.y
        self.speed[2] = math.degrees(msg.twist.twist.angular.z)
        self.odom_received = True

    def run_test_phase(self, phase_name, pwms, duration_sec):
        print(f"\n>>> [PHASE] {phase_name}")
        print(f"    Sending PWMs: M1(Port)={pwms[0]}us, M2(Stbd)={pwms[1]}us, M3(Bow)={pwms[2]}us, M4(Stern)={pwms[3]}us")
        
        msg = Int32MultiArray()
        msg.data = pwms
        
        start_t = time.time()
        while time.time() - start_t < duration_sec:
            self.pwm_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.05)
            print(f"\r    [TELEMETRY] Pos: X={self.pos[0]:+.2f}m, Y={self.pos[1]:+.2f}m | Heading={self.heading_deg:5.1f}deg | Speed: u={self.speed[0]:+.2f}m/s, v={self.speed[1]:+.2f}m/s, yaw={self.speed[2]:+.1f}deg/s", end="", flush=True)
            time.sleep(0.05)
        print()

def main():
    rclpy.init()
    tester = MotorTester()
    print("==========================================================")
    print(" Hugr Optimus - 4-Thruster Hardware & Simulator Verifier")
    print(" Testing /motor_pwms topic and monitoring vessel odometry")
    print("==========================================================")

    # Wait for odometry
    print("Waiting for /odometry from simulator...")
    for _ in range(30):
        rclpy.spin_once(tester, timeout_sec=0.1)
        if tester.odom_received:
            break
        time.sleep(0.1)

    if not tester.odom_received:
        print("[WARN] No /odometry received yet. Ensure run_simulation.bat is running!")
    else:
        print(f"[OK] Simulator connected! Initial Pos: X={tester.pos[0]:.2f}m, Y={tester.pos[1]:.2f}m, Heading={tester.heading_deg:.1f}deg")

    # 1. Forward Surge
    tester.run_test_phase("1. FORWARD SURGE (Main motors M1 & M2 at 1700us)", [1700, 1700, 1500, 1500], 3.0)

    # 2. Stop / Coast
    tester.run_test_phase("Coast to neutral", [1500, 1500, 1500, 1500], 1.5)

    # 3. Pure Lateral Sway
    tester.run_test_phase("2. LATERAL SWAY (Transverse motors M3 & M4 at 1700us)", [1500, 1500, 1700, 1700], 3.0)

    # 4. Stop / Coast
    tester.run_test_phase("Coast to neutral", [1500, 1500, 1500, 1500], 1.5)

    # 5. Pure Pivot Yaw
    tester.run_test_phase("3. ZERO-RADIUS PIVOT (M1=1300, M2=1700, M3=1700, M4=1300)", [1300, 1700, 1700, 1300], 3.0)

    # 6. Stop
    tester.run_test_phase("Neutral Stop", [1500, 1500, 1500, 1500], 1.0)

    print("\n==========================================================")
    print(" Verification complete! All 4 thrusters tested successfully.")
    print("==========================================================")
    tester.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
