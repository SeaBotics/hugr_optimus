#!/usr/bin/env python3
"""
ROS 2 UDP Joy Bridge Node.
Receives gamepad packets over UDP from the Windows host (gamepad_bridge.py)
and publishes them to the standard /joy topic (sensor_msgs/msg/Joy).
Allows seamless controller usage in WSL2 without requiring USBIP or device pass-through.
"""
import socket
import json
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

class UdpJoyNode(Node):
    def __init__(self):
        super().__init__('udp_joy_node')
        self.joy_pub = self.create_publisher(Joy, '/joy', 10)
        
        self.udp_host = "0.0.0.0"
        self.udp_port = 9872
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.udp_host, self.udp_port))
        self.sock.setblocking(False)

        self.timer = self.create_timer(0.02, self.timer_callback) # 50 Hz
        self.get_logger().info(f"UDP Joy Bridge listening on port {self.udp_port} -> Publishing to /joy")

    def timer_callback(self):
        latest_data = None
        while True:
            try:
                data, _ = self.sock.recvfrom(2048)
                latest_data = data
            except BlockingIOError:
                break
            except Exception as e:
                self.get_logger().error(f"Error reading UDP: {e}")
                break

        if latest_data is not None:
            try:
                parsed = json.loads(latest_data.decode('utf-8'))
                msg = Joy()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = "joy"
                msg.axes = [float(a) for a in parsed.get("axes", [])]
                msg.buttons = [int(b) for b in parsed.get("buttons", [])]
                self.joy_pub.publish(msg)

                # Periodic feedback logging
                now_sec = self.get_clock().now().nanoseconds * 1e-9
                if not hasattr(self, '_last_log'):
                    self._last_log = 0.0
                if any(abs(a) > 0.05 for a in msg.axes) and (now_sec - self._last_log >= 1.0):
                    self._last_log = now_sec
                    self.get_logger().info(
                        f"[UDP JOY RECV] Sway={msg.axes[0]:+.2f}, Surge={msg.axes[1]:+.2f}, Yaw={msg.axes[3]:+.2f} -> Published /joy"
                    )
            except Exception as e:
                self.get_logger().warn(f"Failed to parse gamepad packet: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = UdpJoyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
