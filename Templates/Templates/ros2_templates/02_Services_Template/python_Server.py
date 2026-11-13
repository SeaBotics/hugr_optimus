#!/usr/bin/env python3

# Server listenes for request, and gives a response
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
        self.get_logger().info(f"{request.a} + {request.b} = {response.sum}")
        return response                                                                          # Common mistake forget to return a response


def main(args=None):
    rclpy.init(args=args)                 
    node = AddTwoIntsServerNode()                
    rclpy.spin(node)                       
    rclpy.shutdown()                  

if __name__ == "__main__":
    main()    