import rclpy
import serial
from rclpy.node import Node
from sensor_msgs.msg import Joy


class ThrustAllocation(Node):
    # Geometry, body frame: x forward, y starboard
    HALF_BEAM = 0.1575   # |y| of bb/sb thrusters
    BOW_X = 0.25         # x of bow thruster
    DEADZONE = 0.05

    # Set to -1 to reverse a thruster that spins the wrong way
    DIR_FRONT = 1
    DIR_BB = 1
    DIR_SB = 1

    PWM_NEUTRAL = 1500
    PWM_FWD_RANGE = 400  # 1900 at full forward
    PWM_REV_RANGE = 300  # 1200 at full reverse

    AXIS_SURGE = 1       # left stick Y
    AXIS_SWAY = 0        # left stick X
    AXIS_YAW = 3         # right stick X
    BUTTON_Y = 3         # toggle teleop <-> autonomy
    BUTTON_XBOX = 8      # emergency stop

    # Mirrors RobotMode in motor_code.ino
    MODE_TELEOP = 0
    MODE_AUTONOMY = 1
    MODE_EMERGENCY = 2
    MODE_NAMES = {0: 'TELEOP', 1: 'AUTONOMY', 2: 'EMERGENCY'}

    def __init__(self):
        super().__init__('thrust_allocation')
        self.create_subscription(Joy, 'joy', self.on_joy, 10)
        self.mode = self.MODE_TELEOP
        self.prev_y = 0
        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def on_joy(self, msg):
        # Arduino stops reading serial in emergency; keep write() from blocking
        if self.mode == self.MODE_EMERGENCY:
            return

        mode_swap, emergency = self.handle_buttons(msg.buttons)

        # ROS joy: stick up and left are positive
        surge = self.deadzone(msg.axes[self.AXIS_SURGE])
        sway = self.deadzone(-msg.axes[self.AXIS_SWAY])
        yaw = self.deadzone(-msg.axes[self.AXIS_YAW])

        front, bb, sb = self.allocate(surge, sway, yaw)
        line = f"{front},{bb},{sb},{mode_swap},{emergency}"
        self.get_logger().info(line)
        self.ser.write((line + "\n").encode())

    def handle_buttons(self, buttons):
        y = buttons[self.BUTTON_Y] if len(buttons) > self.BUTTON_Y else 0
        xbox = buttons[self.BUTTON_XBOX] if len(buttons) > self.BUTTON_XBOX else 0

        # Arduino toggles on every mode_swap == 1, so send only on press
        mode_swap = 1 if (y and not self.prev_y) else 0
        self.prev_y = y
        emergency = 1 if xbox else 0

        if emergency:
            self.mode = self.MODE_EMERGENCY
        elif mode_swap:
            self.mode = (self.MODE_AUTONOMY if self.mode == self.MODE_TELEOP
                         else self.MODE_TELEOP)
        if mode_swap or emergency:
            self.get_logger().warn(f"Mode -> {self.MODE_NAMES[self.mode]}")

        return mode_swap, emergency

    def deadzone(self, x):
        return 0.0 if abs(x) <= self.DEADZONE else x

    def allocate(self, surge, sway, yaw):
        """surge: + forward, sway: + starboard, yaw: + turn to starboard. All in [-1, 1]."""
        # Bb/sb differential cancels the yaw moment from the bow thruster
        diff = yaw - sway * self.BOW_X / (2 * self.HALF_BEAM)
        t_front = sway
        t_bb = surge + diff
        t_sb = surge - diff

        peak = max(abs(t_front), abs(t_bb), abs(t_sb))
        if peak > 1.0:
            t_front, t_bb, t_sb = t_front / peak, t_bb / peak, t_sb / peak

        return (self.to_pwm(self.DIR_FRONT * t_front),
                self.to_pwm(self.DIR_BB * t_bb),
                self.to_pwm(self.DIR_SB * t_sb))

    def to_pwm(self, x):
        rng = self.PWM_FWD_RANGE if x >= 0.0 else self.PWM_REV_RANGE
        return round(self.PWM_NEUTRAL + rng * x)


def main(args=None):
    rclpy.init(args=args)
    node = ThrustAllocation()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
