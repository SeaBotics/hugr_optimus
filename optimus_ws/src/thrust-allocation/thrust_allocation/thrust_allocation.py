import rclpy
import serial
from rclpy.node import Node
from sensor_msgs.msg import Joy

class ThrustAllocation(Node):
    # Boat parameters PRIMUS
    MASS = 35.0
    D1X = 0.35
    D1Y = 0.1575
    D2X = 0.35
    D2Y = -0.1575
    D3X = 0.25
    D3Y = 0.35
    DEADZONE = 0.05

    def __init__(self):
        super().__init__('thrust_allocation')
        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.controller_allocation,
            10)
        
        # Thurster parameters
        self.t1 = 1500
        self.t2 = 1500
        self.t3 = 1500
        # Controller parameters
        self.tau = 0.0
        self.Fx = 0.0
        self.Fy = 0.0
        # Serial
        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def controller_allocation(self, msg):
        self.Fx = -msg.axes[1]
        self.Fy = -msg.axes[0]
        self.tau = -msg.axes[3]

        if(abs(self.Fx)  <= self.DEADZONE):
            self.Fx = 0.0
        if(abs(self.Fy)  <= self.DEADZONE):
            self.Fy = 0.0
        if(abs(self.tau) <= self.DEADZONE):
            self.tau = 0.0

        self.thrusterForce()        

    def scaleJoystick(self, x):
        if x >= 0.0:
            return round(1500 + 400*x)
        else:
            return round(1500 + 200*x)

    def thrusterForce(self):
        self.t1 = 2*self.Fx * ((self.D2Y)/(self.D2Y - self.D1Y)) + self.Fy * (self.D3X/(self.D2Y - self.D1Y)) - self.tau/3 * (1/(self.D2Y - self.D1Y))
        self.t2 = - 2*self.Fx * ((self.D1Y)/(self.D2Y- self.D1Y)) - self.Fy* (self.D3X/(self.D2Y - self.D1Y)) + self.tau/3 * (1/(self.D2Y - self.D1Y))
        self.t3 = self.Fy

        maxThrust = max(abs(self.t1), abs(self.t2), abs(self.t3))

        if(maxThrust > 1.0):
            self.t1 /= maxThrust
            self.t2 /= maxThrust
            self.t3 /= maxThrust

        self.t1 = self.scaleJoystick(self.t1)
        self.t2 = self.scaleJoystick(self.t2)
        self.t3 = self.scaleJoystick(self.t3)
        
        info = f"{self.t1},{self.t2},{self.t3}\n"
        self.get_logger().info(info)
        output = f"{self.t1},{self.t2},{self.t3}\n".encode()
        self.ser.write(output)

def main(args=None):
    rclpy.init(args=args)
    thrust_allocation = ThrustAllocation()
    rclpy.spin(thrust_allocation)
    
    thrust_allocation.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()