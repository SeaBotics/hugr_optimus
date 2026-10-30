#!/usr/bin/env python3
"""
ROS 2 Receiver for Windows Gamepad Bridge.
Listens on HTTP port 8085 for gamepad commands from the Windows host,
publishes directly to /motor_pwms, /cmd_vel, and /joy,
and replies with live vessel odometry from the Fossen simulator.
"""

import sys
import json
import math
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Float32MultiArray
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Joy

TELEMETRY = {
    "pos": {"x": 0.0, "y": 0.0, "z": 0.0},
    "heading_deg": 0.0,
    "roll_deg": 0.0,
    "pitch_deg": 0.0,
    "speed": {"u": 0.0, "v": 0.0, "yaw_rate": 0.0},
    "thrusts": [0.0, 0.0, 0.0, 0.0],
    "last_odom_time": 0.0
}

ROS_BRIDGE_NODE = None

class GamepadReceiverNode(Node):
    def __init__(self):
        super().__init__('gamepad_receiver_node')
        self.pwm_pub = self.create_publisher(Int32MultiArray, '/motor_pwms', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.joy_pub = self.create_publisher(Joy, '/joy', 10)
        
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)
        self.thrust_sub = self.create_subscription(Float32MultiArray, '/thrusters/actual_thrust', self.thrust_callback, 10)
        
        self.last_log_t = 0.0
        self.get_logger().info("Gamepad ROS 2 Receiver started. Ready to receive commands from Windows.")

    def odom_callback(self, msg: Odometry):
        TELEMETRY["pos"]["x"] = round(float(msg.pose.pose.position.x), 2)
        TELEMETRY["pos"]["y"] = round(float(msg.pose.pose.position.y), 2)
        TELEMETRY["pos"]["z"] = round(float(msg.pose.pose.position.z), 2)

        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        TELEMETRY["heading_deg"] = round(math.degrees(math.atan2(siny_cosp, cosy_cosp)) % 360.0, 1)

        sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        TELEMETRY["roll_deg"] = round(math.degrees(math.atan2(sinr_cosp, cosr_cosp)), 1)

        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        TELEMETRY["pitch_deg"] = round(math.degrees(math.asin(max(-1.0, min(1.0, sinp)))), 1)

        TELEMETRY["speed"]["u"] = round(float(msg.twist.twist.linear.x), 2)
        TELEMETRY["speed"]["v"] = round(float(msg.twist.twist.linear.y), 2)
        TELEMETRY["speed"]["yaw_rate"] = round(math.degrees(float(msg.twist.twist.angular.z)), 1)
        TELEMETRY["last_odom_time"] = time.time()

    def thrust_callback(self, msg: Float32MultiArray):
        if len(msg.data) >= 4:
            TELEMETRY["thrusts"] = [round(float(v), 1) for v in msg.data[:4]]

    def publish_commands(self, pwms, surge, sway, yaw, axes, buttons):
        # 1. Publish /motor_pwms
        pwm_msg = Int32MultiArray()
        pwm_msg.data = [int(p) for p in pwms]
        self.pwm_pub.publish(pwm_msg)

        # 2. Publish /cmd_vel
        twist_msg = Twist()
        twist_msg.linear.x = float(surge) * 1.5   # Scale to m/s
        twist_msg.linear.y = float(sway) * 1.0
        twist_msg.angular.z = float(yaw) * 1.0   # rad/s
        self.cmd_vel_pub.publish(twist_msg)

        # 3. Publish /joy
        joy_msg = Joy()
        joy_msg.header.stamp = self.get_clock().now().to_msg()
        joy_msg.header.frame_id = "joy"
        joy_msg.axes = [float(a) for a in axes]
        joy_msg.buttons = [int(b) for b in buttons]
        self.joy_pub.publish(joy_msg)

        # Throttled logging to terminal
        now = time.time()
        is_active = any(p != 1500 for p in pwms)
        if is_active and (now - self.last_log_t >= 0.5):
            self.get_logger().info(
                f"[GAMEPAD -> /motor_pwms] M1={pwms[0]}, M2={pwms[1]}, M3={pwms[2]}, M4={pwms[3]} "
                f"| In: Surge={surge:+.2f}, Sway={sway:+.2f}, Yaw={yaw:+.2f} "
                f"| Vessel: Vel={TELEMETRY['speed']['u']:.2f}m/s, Heading={TELEMETRY['heading_deg']:.1f}° "
                f"| Waves: Roll={TELEMETRY['roll_deg']:+.1f}°, Pitch={TELEMETRY['pitch_deg']:+.1f}°, Z={TELEMETRY['pos']['z']:+.2f}m"
            )

class HttpHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress routine HTTP logs

    def do_POST(self):
        if self.path == '/api/gamepad':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                data = json.loads(body)

                pwms = data.get("pwms", [1500, 1500, 1500, 1500])
                surge = data.get("surge", 0.0)
                sway = data.get("sway", 0.0)
                yaw = data.get("yaw", 0.0)
                axes = data.get("axes", [])
                buttons = data.get("buttons", [])

                if ROS_BRIDGE_NODE is not None:
                    ROS_BRIDGE_NODE.publish_commands(pwms, surge, sway, yaw, axes, buttons)

                # Return live vessel telemetry back to Windows
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                resp = json.dumps({"status": "ok", "telemetry": TELEMETRY}).encode('utf-8')
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8085):
    server = HTTPServer(('0.0.0.0', port), HttpHandler)
    server.serve_forever()

def main():
    global ROS_BRIDGE_NODE
    rclpy.init()
    ROS_BRIDGE_NODE = GamepadReceiverNode()

    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_server, args=(8085,), daemon=True)
    http_thread.start()

    print("==========================================================")
    print(" Hugr Optimus - Gamepad ROS 2 Bridge Receiver")
    print(" Receiving Windows Gamepad on port 8085")
    print(" Publishing directly to: /motor_pwms, /cmd_vel, /joy")
    print("==========================================================")

    try:
        rclpy.spin(ROS_BRIDGE_NODE)
    except KeyboardInterrupt:
        pass
    finally:
        ROS_BRIDGE_NODE.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
