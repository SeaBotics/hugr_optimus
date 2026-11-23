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

    # Xbox controller button indices on /joy
    BUTTON_Y = 3      # Toggle teleop <-> autonomy
    BUTTON_XBOX = 8   # Emergency stop

    # Mirrors RobotMode in motor_code.ino
    MODE_TELEOP = 0
    MODE_AUTONOMY = 1
    MODE_EMERGENCY = 2
    MODE_NAMES = {0: 'TELEOP', 1: 'AUTONOMY', 2: 'EMERGENCY'}

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
        # Mode handling
        self.mode = self.MODE_TELEOP   # Local mirror of the Arduino's mode
        self.prev_y = 0                # Previous Y button state, for edge detection
        self.mode_swap = 0             # 1 for exactly one message per Y press
        self.emergency = 0
        # Serial
        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def controller_allocation(self, msg):
        # The Arduino latches emergency and stops reading serial, so stop
        # sending as well; otherwise the serial buffer fills and write() blocks.
        if self.mode == self.MODE_EMERGENCY:
            return

        self.handleButtons(msg)

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

    def handleButtons(self, msg):
        buttons = msg.buttons
        y = buttons[self.BUTTON_Y] if len(buttons) > self.BUTTON_Y else 0
        xbox = buttons[self.BUTTON_XBOX] if len(buttons) > self.BUTTON_XBOX else 0

        # The Arduino toggles mode on every message with mode_swap == 1,
        # so only send it on the press (rising edge), not while Y is held.
        self.mode_swap = 1 if (y == 1 and self.prev_y == 0) else 0
        self.prev_y = y

        self.emergency = 1 if xbox == 1 else 0

        if self.emergency:
            self.mode = self.MODE_EMERGENCY
        elif self.mode_swap:
            self.mode = (self.MODE_AUTONOMY if self.mode == self.MODE_TELEOP
                         else self.MODE_TELEOP)

        if self.mode_swap or self.emergency:
            self.get_logger().warn(f"Mode -> {self.MODE_NAMES[self.mode]}")

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
        
        # Format expected by motor_code.ino: "front,bb,sb,mode_swap,emergency\n"
        info = f"{self.t1},{self.t2},{self.t3},{self.mode_swap},{self.emergency}"
        self.get_logger().info(info)
        self.ser.write((info + "\n").encode())

def main(args=None):
    rclpy.init(args=args)
    thrust_allocation = ThrustAllocation()
    rclpy.spin(thrust_allocation)
    
    thrust_allocation.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
