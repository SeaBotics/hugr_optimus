# Service
# uses .srv not msg

# Use a Server and clinet relation
# We can have multiple clients for the service, but only one node for the service itself.

# Where as topics use the pub/sub, services use Request/Respone
# You send a request, it processes, and returns a answer.

# Can be synchronous or asynchronous

# ---------- Example ----------

# ---------- Server ----------

#!/usr/bin/env python3

import rclpy 
from rclpy.node import Node               
from example_interfaces.srv import AddTwoInts

class AddTwoIntsServerNode(Node):
    def __init__(self):
        super().__init__("add_two_ints_server") 

        self.server_ = self.create_service(AddTwoInts, "add_two_ints", self.callback_add_two_ints)   # Tips use verb for services
        self.get_logger().info("Add two Ints Server has been started.")

    def callback_add_two_ints(self, request: AddTwoInts.Request, response: AddTwoInts.Response):
        response.sum = request.a + request.b
        self.get_logger().info(str(request.a) + " + " + str(request.b) + " = " + str(response.sum))
        return response                                                                          # Common mistake forget to return a response
 

def main(args=None):
    rclpy.init(args=args)                 
    node = AddTwoIntsServerNode()                
    node.get_logger().info("Hello ROS2")  
    rclpy.spin(node)                       
    rclpy.shutdown()                  

if __name__ == "__main__":
    main()             

# ---------- Client ----------

#!/usr/bin/env python3

import rclpy 
from rclpy.node import Node              
from example_interfaces.srv import AddTwoInts

class AddTwoIntsClientNode(Node):
    def __init__(self):
        super().__init__("add_two_ints_clients")
        self.client_ = self.create_client(AddTwoInts, "add_two_ints")
        
        while not self.client_.wait_for_service(1.0):
            self.get_logger().warn("Waiting for servername...")

    def send_request(self, a, b):
        self.request = AddTwoInts.Request()
        self.request.a = a
        self.request.b = b
        self.future = self.client_.call_async(self.request)
        return self.future

def main(args=None):
    rclpy.init(args=args)                 
    node = AddTwoIntsClientNode()    

    # Sender forespørsel (3 og 8) og returnerer future-objektet
    future = node.send_request(3, 8)
    
    # Spinner noden til svaret er mottatt
    rclpy.spin_until_future_complete(node, future)

    response = future.result()
    node.get_logger().info(str(node.request.a) + " + " + str(node.request.b) + " = " + str(response.sum))
    
    rclpy.shutdown()                  

if __name__ == "__main__":
    main()