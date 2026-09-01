#!/usr/bin/env python3
import rclpy                                 # Imports the ROS 2 client library that gives us ROS 2 functionalities
from rclpy.node import Node                  # Imports Node class - base class for all ROS 2 nodes
from sensor_msgs.msg import CompressedImage  # Imports CompressedImage message type from our camera videostream topic

class Detector(Node):                        # Create a class "Detector" that inherits from Node (standard ROS 2 pattern)
    def __init__(self):                      # Constructor - runs once when node is created
        super().__init__("detector")         # Call parent class constructor, initialize node named "detector"
                                             # The "detector" is the node name in "ros2 node list"
        self.frame_count = 0                 # Initialize frame counter as class variable (accessible in callback)
                                             # Keeps count alive between each callback execution
        
        # Create subscriber: listen to /image_raw/compressed topic
        # When message arrives, run self.callback function automatically
        # Queue size 10 means buffer up to 10 messages 
        self.create_subscription(CompressedImage, "/image_raw/compressed", self.callback, 10)
        self.get_logger().info("Detector started, listening to /image_raw/compressed")  # Log startup message to terminal
    
    def callback(self, msg):                 # Callback function - runs every time CompressedImage message arrives
                                             # This runs ~30 times per second (your camera frame rate)
        self.frame_count += 1                # Increment counter each time frame arrives
        self.get_logger().info(f"Frame {self.frame_count} received")  # Log frame number to terminal

def main(args=None):                         # Main entry point function
    rclpy.init(args=args)                    # Wake up ROS 2 - first thing to do, initializes ROS 2
    node = Detector()                        # Create instance of Detector node - subscription starts immediately
    rclpy.spin(node)                         # Spin node alive - blocks here forever, waits for messages, runs callbacks
                                             # Without this, program exits immediately
    rclpy.shutdown()                         # Cleanup when Ctrl+C pressed - shutdown ROS 2 gracefully

if __name__ == "__main__":                   # Standard Python pattern: only run main() if script executed directly
    main()