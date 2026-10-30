#!/usr/bin/env python3
"""
Node: mock_mode_publisher
Package: signal_tower
Author: Julian (SeaBotics)

Helper test node to simulate Task 2 (Operating Modes).
Cycles through:
1. safe_stop (for 3s)
2. manual (for 3s)
3. autonomous (for 3s)
4. simulates communication loss / crash to verify Watchdog fail-safe.
"""

import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MockModePublisher(Node):
    def __init__(self):
        super().__init__("mock_mode_publisher")
        self.publisher_ = self.create_publisher(String, "/system/mode", 10)
        self.timer = self.create_timer(1.0, self.publish_mode)
        self.step = 0
        self.get_logger().info("Mock Mode Publisher started. Cycling modes for Task 3 verification.")

    def publish_mode(self):
        self.step += 1
        msg = String()

        if 1 <= self.step <= 3:
            msg.data = "safe_stop"
        elif 4 <= self.step <= 6:
            msg.data = "manual"
        elif 7 <= self.step <= 9:
            msg.data = "autonomous"
        elif self.step == 10:
            self.get_logger().warn(">>> SIMULATING COMMUNICATION LOSS: Stopping publication to trigger Watchdog <<<")
            self.timer.cancel()
            return

        self.publisher_.publish(msg)
        self.get_logger().info(f"[SIM SYSTEM] Published mode: '{msg.data}' (step {self.step}/10)")


def main(args=None):
    rclpy.init(args=args)
    node = MockModePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
