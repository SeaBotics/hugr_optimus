#!/usr/bin/env python3

import rclpy 
from rclpy.node import Node          
from std_msgs.msg import String              

class MyNode(Node):                                 
    def __init__(self):
        super().__init__("py_test")                  
        
        self.counter = 0                             
        self.get_logger().info("Hello ROS2")         

        # ---------- Publisher ----------

        self.publisher_ = self.create_publisher(String, "example_topic", 10) # Buffer important for data

        # ---------- Subscriber ----------

        self.subscription = self.create_subscription(
            String, 
            "example_topic", 
            self.listener_callback, 
            10
        )

        self.create_timer(1.0, self.timer_callback)  
        
    def timer_callback(self):                 # Callback function for subscribing/publishing    

        msg = String()
        msg.data = f"Hello ROS2 Network: {self.counter}"
        self.publisher_.publish(msg)

        self.get_logger().info("Hello")
        self.counter += 1

    def listener_callback(self, msg):         # Callback function for subscribing
        self.get_logger().info(f"Subscribed Listener Heard: '{msg.data}'")

def main(args=None):
    rclpy.init(args=args)                                     
    node = MyNode()                                  
    rclpy.spin(node)                                 
    rclpy.shutdown()                               
if __name__ == "__main__":                
    main()  