import rclpy
import serial
from rclpy.node import Node
from sensor_msgs.msg import Joy


class ThrustAllocation(Node):
    # --- Field tuning: flip to -1 if something goes the wrong way ---
    # Joystick -> force
    SIGN_FX = 1     # left stick Y, surge
    SIGN_FY = -1    # left stick X, sway
    SIGN_TAU = -1   # right stick X, yaw
    # Thruster spin direction
    DIR_FRONT = 1
    DIR_BB = 1
    DIR_SB = 1

    # Boat parameters PRIMUS
    MASS = 35.0
    D1X = 0.35
    D1Y = 0.1575
    D2X = 0.35
    D2Y = -0.1575
    D3X = 0.25
    D3Y = 0.35
    DEADZONE = 0.05

    # PWM
    PWM_NEUTRAL = 1500
    PWM_FWD_RANGE = 400   # 1900 at full forward
    PWM_REV_RANGE = 300   # 1200 at full reverse

    # Xbox controller indices on /joy
    AXIS_FX = 1       # left stick Y
    AXIS_FY = 0       # left stick X
    AXIS_TAU = 3      # right stick X
    BUTTON_Y = 3      # toggle teleop <-> autonomy
    BUTTON_XBOX = 8   # emergency stop

    # Mirrors RobotMode in motor_code.ino
    MODE_TELEOP = 0
    MODE_AUTONOMY = 1
    MODE_EMERGENCY = 2
    MODE_NAMES = {0: 'TELEOP', 1: 'AUTONOMY', 2: 'EMERGENCY'}

    def __init__(self):
        super().__init__('thrust_allocation')
        self.subscription = self.create_subscription(
            Joy, 'joy', self.controller_allocation, 10)

        # Thruster commands, normalized [-1, 1]
        self.t1 = 0.0   # bb
        self.t2 = 0.0   # sb
        self.t3 = 0.0   # front
        # Controller inputs
        self.Fx = 0.0
        self.Fy = 0.0
        self.tau = 0.0
        # Mode handling
        self.mode = self.MODE_TELEOP
        self.prev_y = 0
        self.mode_swap = 0
        self.emergency = 0

        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def controller_allocation(self, msg):
        # Arduino stops reading serial in emergency; keep write() from blocking
        if self.mode == self.MODE_EMERGENCY:
            return

        self.handleButtons(msg)

        self.Fx = self.deadzone(self.SIGN_FX * msg.axes[self.AXIS_FX])
        self.Fy = self.deadzone(self.SIGN_FY * msg.axes[self.AXIS_FY])
        self.tau = self.deadzone(self.SIGN_TAU * msg.axes[self.AXIS_TAU])

        self.thrusterForce()
        self.sendSerial()

    def handleButtons(self, msg):
        buttons = msg.buttons
        y = buttons[self.BUTTON_Y] if len(buttons) > self.BUTTON_Y else 0
        xbox = buttons[self.BUTTON_XBOX] if len(buttons) > self.BUTTON_XBOX else 0

        # Arduino toggles on every mode_swap == 1, so send only on press
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

    def deadzone(self, x):
        return 0.0 if abs(x) <= self.DEADZONE else x

    def thrusterForce(self):
        self.t1 = 2*self.Fx * ((self.D2Y)/(self.D2Y - self.D1Y)) + self.Fy * (self.D3X/(self.D2Y - self.D1Y)) - self.tau/3 * (1/(self.D2Y - self.D1Y))
        self.t2 = - 2*self.Fx * ((self.D1Y)/(self.D2Y - self.D1Y)) - self.Fy * (self.D3X/(self.D2Y - self.D1Y)) + self.tau/3 * (1/(self.D2Y - self.D1Y))
        self.t3 = self.Fy

        maxThrust = max(abs(self.t1), abs(self.t2), abs(self.t3))
        if maxThrust > 1.0:
            self.t1 /= maxThrust
            self.t2 /= maxThrust
            self.t3 /= maxThrust

    def scaleJoystick(self, x):
        if x >= 0.0:
            return round(self.PWM_NEUTRAL + self.PWM_FWD_RANGE*x)
        else:
            return round(self.PWM_NEUTRAL + self.PWM_REV_RANGE*x)

    def sendSerial(self):
        front = self.scaleJoystick(self.DIR_FRONT * self.t3)
        bb = self.scaleJoystick(self.DIR_BB * self.t1)
        sb = self.scaleJoystick(self.DIR_SB * self.t2)

        # Format expected by motor_code.ino: "front,bb,sb,mode_swap,emergency\n"
        info = f"{front},{bb},{sb},{self.mode_swap},{self.emergency}"
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
