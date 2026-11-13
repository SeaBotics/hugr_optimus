#!/usr/bin/env python3
"""
CLI Tool to send navigation destinations to Hugr Optimus ASV
Supports:
 - Local metric coordinates: --x 15.0 --y 20.0
 - GPS geodetic coordinates: --lat 58.33425 --lon 8.57845
 - Cancellation: --cancel
"""

import sys
import argparse
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import Empty, String

class DestinationSender(Node):
    def __init__(self):
        super().__init__('destination_sender')
        self.pose_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.gps_pub = self.create_publisher(NavSatFix, '/destination_gps', 10)
        self.circuit_pub = self.create_publisher(Empty, '/autonomous/start_circuit', 10)
        self.cancel_pub = self.create_publisher(Empty, '/cancel_destination', 10)
        self.status_sub = self.create_subscription(String, '/autonomous/status', self.status_cb, 10)
        self.latest_status = None

    def status_cb(self, msg):
        self.latest_status = msg.data

def main():
    parser = argparse.ArgumentParser(description="Send navigation destinations to Hugr Optimus ASV")
    parser.add_argument('--circuit', action='store_true', help="Start full autonomous competition buoy circuit")
    parser.add_argument('--x', type=float, help="Target X coordinate in meters (East)")
    parser.add_argument('--y', type=float, help="Target Y coordinate in meters (North)")
    parser.add_argument('--lat', type=float, help="Target GPS Latitude (decimal degrees)")
    parser.add_argument('--lon', type=float, help="Target GPS Longitude (decimal degrees)")
    parser.add_argument('--cancel', action='store_true', help="Cancel current autonomous mission and stop vessel")

    args = parser.parse_args()

    rclpy.init()
    node = DestinationSender()

    # Small spin to ensure ROS 2 DDS discovery
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=0.05)

    if args.cancel:
        print("[!] Sending Emergency/Mission CANCEL command...")
        node.cancel_pub.publish(Empty())
        print("[✓] Cancel command published. Vessel will stop.")
    elif args.circuit:
        print("[🏁] Sending START BUOY COMPETITION CIRCUIT command...")
        node.circuit_pub.publish(Empty())
        print("[✓] Full 9-waypoint competition circuit activated!")
    elif args.x is not None and args.y is not None:
        print(f"[→] Sending Metric Destination: X = {args.x:.2f} m, Y = {args.y:.2f} m")
        msg = PoseStamped()
        msg.header.frame_id = 'odom'
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.pose.position.x = float(args.x)
        msg.pose.position.y = float(args.y)
        msg.pose.position.z = 0.0
        msg.pose.orientation.w = 1.0
        node.pose_pub.publish(msg)
        print("[✓] Metric goal published to /goal_pose")
    elif args.lat is not None and args.lon is not None:
        print(f"[→] Sending GPS Destination: Lat = {args.lat:.6f}°, Lon = {args.lon:.6f}°")
        msg = NavSatFix()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.latitude = float(args.lat)
        msg.longitude = float(args.lon)
        node.gps_pub.publish(msg)
        print("[✓] GPS goal published to /destination_gps")
    else:
        print("Usage error: You must provide either (--x and --y) OR (--lat and --lon) OR --cancel")
        parser.print_help()
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    # Allow network transmission
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
