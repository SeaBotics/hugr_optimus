# This document describes syntax and template for a ros2 node
# Remember python code is made in the same folder as __init__.py file
# chmod +x makes it an executable
# 

# Topics use .msg

# See this: https://docs.ros.org/en/jazzy/p/rclpy/
# See this: https://github.com/ros2/rclpy

# ----------- Code starts here -----------

#!/usr/bin/env python3 <- this is a shebang line, it tells the system that this file should be run with python3 interpreter
# remember shebang in top of document always
import rclpy 
from rclpy.node import Node               # only one import pr. line is allowed

def main(args=None):
    rclpy.init(args=args)                 # Initialize the ROS2 communication
    node = Node("my_test")                # See that the node is here, not the python file itself
    node.get_logger().info("Hello ROS2")  # Log a message to the console
    rclpy.spin(node)                       # Keeps the node alive until Ctrl+C
    rclpy.shutdown()                      # Shutdown the ROS2 communication

if __name__ == "__main__":                # Checks if the script is being executed directly from the terminal rather than being imported as a module by another script.
    main()                                # Executes the main function when the script is run directly.

# In the terminal after running it you would get a: [info][timestamp][node_name] corresponding to line 13 and 14
# Important after making a node add it to the "Entry points" in the setup.py
# Remember that colcon build will place the executables in install folder
# Easy to get confused because the node is defined on line 13, but it does not need to have the same name as the package, and also in setup.py the node_name can be called something else. Good place to troubleshoot.

# ----------- Code with Classes (Recomended by ROS2) Template -----------
import rclpy 
from rclpy.node import Node               

class MyNode(Node):                                  # MyNode is the node name
    def __init__(self):
        super().__init__("py_test")                  # "py_test" is the node-name in the ros2 graph
        
        self.counter = 0                             # State variable to track execution ticks
        self.get_logger().info("Hello ROS2")         # Log node initialization status to stdout/rosout
        self.create_timer(1.0, self.timer_callback)  # Register a periodic timer behavior, Adds the timer to the global executor loop
        
    def timer_callback(self):                        # Timer allows to execute a command every n amount of time
        self.get_logger().info("Hello")
        self.counter += 1

def main(args=None):
    rclpy.init(args=args)                            # Initialize the ROS2 communications middleware layer (RMW)         
    node = MyNode()                                  # Instantiate the node executor target

    # It pauses the main script: It stops the code from reaching the end of the file so your program doesn't close.
    # It enters a "listening" loop: It constantly checks, "Is it time to run the timer yet?" or "Did we get a new message?"
    # It triggers your actions: The moment 1.0 second passes, spin() spots it and instantly runs your timer_callback function.
    rclpy.spin(node)                                 


    rclpy.shutdown()                                 # Context destruction: release ROS2 resources, destroy nodes, shutdown middleware

if __name__ == "__main__":                
    main()  

# Only prints text to its own terminal window. It does not broadcast any data across the ROS2 network. Other nodes cannot see or hear it.
# Therefore this next example includes the core ros2 functionality of publish/subscribe

import rclpy 
from rclpy.node import Node          
from std_msgs.msg import String              # Import standard ROS2 primitive message types

class MyNode(Node):                                 
    def __init__(self):
        super().__init__("py_test")                  
        
        self.counter = 0                             
        self.get_logger().info("Hello ROS2")         

        # ---------- Publisher ----------

        # Publisher: Creates a pipe named "/example_topic" using String messages.
        # Queue size (n) buffers outgoing messages if network latency peaks.
        self.publisher_ = self.create_publisher(String, "example_topic", 10)

        # ---------- Subscriber ----------

        # Subscriber: Listens to "/example_topic". 
        # Whenever a message arrives, the executor interrupts to run 'listener_callback'.
        self.subscription = self.create_subscription(
            String, 
            "example_topic", 
            self.listener_callback, 
            10
        )

        # Note; A package can have its node subscribe to n amount of topics, and pubish to m amount of topics

        self.create_timer(1.0, self.timer_callback)  
        
    def timer_callback(self):                     

        # Construct the standard ROS2 message object
        msg = String()
        msg.data = f"Hello ROS2 Network: {self.counter}"

        # Broadcast the data across the active DDS network
        self.publisher_.publish(msg)

        self.get_logger().info("Hello")
        self.counter += 1

    def listener_callback(self, msg):
        # Asynchronous event handler triggered when data arrives on monitored topic
        self.get_logger().info(f"Subscribed Listener Heard: '{msg.data}'")

def main(args=None):
    rclpy.init(args=args)                                     
    node = MyNode()                                  
    rclpy.spin(node)                                 
    rclpy.shutdown()                               
if __name__ == "__main__":                
    main()  