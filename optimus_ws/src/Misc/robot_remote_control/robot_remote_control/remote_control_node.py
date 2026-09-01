#!/usr/bin/env python3
"""Xbox controller -> joint-space jogging of the DOFBOT arm.

Reads /joy from game_controller_node, integrates each configured axis or
button pair into a joint position, and streams the result as single-point
JointTrajectory messages to the trajectory controllers that are already
running.

Everything here is in URDF units: radians for servo1..servo5, metres for the
gripper. Servo IDs, degrees, I2C counts and the gripper curve are none of
this node's business -- robot_hardware owns all of that.

The whole mapping lives in config/joystick_config.yaml. Nothing in this file
needs editing to change which stick drives which joint.

Do not jog while MoveIt is executing a plan. Both write the same trajectory
buffer in the controller, and the interleaving is undefined.
"""

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState, Joy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


class RemoteControlNode(Node):

    def __init__(self):
        super().__init__("remote_control_node")

        declare = self.declare_parameter

        self.rate_hz = declare("rate_hz", 50.0).value
        self.dt = 1.0 / self.rate_hz
        self.lookahead = declare("lookahead", 2.0).value
        self.joy_timeout = declare("joy_timeout", 0.25).value
        self.deadman_button = declare("deadman_button", 0).value

        arm_controller = declare("arm_controller", "main_controller").value
        gripper_controller = declare(
            "gripper_controller", "gripper_controller").value

        self.arm_joints = declare(
            "arm_joints",
            ["servo1", "servo2", "servo3", "servo4", "servo5"]).value
        self.gripper_joint = declare(
            "gripper_joint", "gripper_left_finger_joint").value

        # An unset index is -1, which every lookup below reads as "no source".
        self.mapping = {
            name: {
                "axis": declare(f"{name}.axis", -1).value,
                "plus_button": declare(f"{name}.plus_button", -1).value,
                "minus_button": declare(f"{name}.minus_button", -1).value,
                "scale": declare(f"{name}.scale", 0.0).value,
                "lower": declare(f"{name}.lower", -1.5).value,
                "upper": declare(f"{name}.upper", 1.5).value,
            }
            for name in self.arm_joints + [self.gripper_joint]
        }

        self.arm_publisher = self.create_publisher(
            JointTrajectory, f"{arm_controller}/joint_trajectory", 1)
        self.gripper_publisher = self.create_publisher(
            JointTrajectory, f"{gripper_controller}/joint_trajectory", 1)

        self.create_subscription(Joy, "joy", self.on_joy, 1)
        self.create_subscription(
            JointState, "joint_states", self.on_joint_states, 10)
        self.create_timer(self.dt, self.on_timer)

        self.measured = {}          # latest /joint_states, name -> position
        self.target = None          # integrated setpoints, None until seeded
        self.joy = None
        self.joy_received_at = 0.0
        self.deadman_was_held = False
        self.joy_validated = False

        self.get_logger().info(
            f"{len(self.arm_joints)} arm joints at {self.rate_hz:.0f} Hz, "
            f"hold button {self.deadman_button} to move")

    # --- inputs -----------------------------------------------------------

    def on_joint_states(self, message):
        self.measured = dict(zip(message.name, message.position))

    def on_joy(self, message):
        if not self.joy_validated:
            self.validate_indices(message)
            self.joy_validated = True
        self.joy = message
        self.joy_received_at = self.get_clock().now().nanoseconds * 1e-9

    def validate_indices(self, joy):
        """Check every configured index against the pad we actually got.

        Worth doing once, loudly: an index past the end of the array reads as
        a permanently centred axis or an unpressable button. The joint simply
        never moves, and there is nothing in the logs to explain why.
        """
        problems = []
        for name, entry in self.mapping.items():
            if entry["axis"] >= len(joy.axes):
                problems.append(f"{name}.axis={entry['axis']}")
            for key in ("plus_button", "minus_button"):
                if entry[key] >= len(joy.buttons):
                    problems.append(f"{name}.{key}={entry[key]}")
            if entry["axis"] < 0 and entry["plus_button"] < 0 \
                    and entry["minus_button"] < 0:
                problems.append(f"{name} has no axis or button pair")
        if self.deadman_button >= len(joy.buttons):
            problems.append(f"deadman_button={self.deadman_button}")

        if problems:
            self.get_logger().error(
                f"controller reports {len(joy.axes)} axes and "
                f"{len(joy.buttons)} buttons; unusable configuration: "
                + ", ".join(problems))

    def button(self, joy, index):
        return 1 if 0 <= index < len(joy.buttons) and joy.buttons[index] else 0

    def velocity_command(self, joy, entry):
        """Normalised -1..1 from whichever source the joint is configured for.

        An axis is proportional, a button pair is on/off. Both are read, so a
        joint given both simply sums them; the config documents one or the
        other.
        """
        command = 0.0
        axis = entry["axis"]
        if 0 <= axis < len(joy.axes):
            command += joy.axes[axis]
        command += self.button(joy, entry["plus_button"])
        command -= self.button(joy, entry["minus_button"])
        return clamp(command, -1.0, 1.0)

    # --- cycle ------------------------------------------------------------

    def seed_from_measured(self):
        """Start integrating from where the arm is, not from zero.

        Re-read on every deadman press, so a MoveIt motion made in between is
        picked up instead of jumping back to the last jogged pose.
        """
        names = self.arm_joints + [self.gripper_joint]
        missing = [name for name in names if name not in self.measured]
        if missing:
            self.get_logger().warn(
                f"no joint_states for {missing} -- is the controller running?",
                throttle_duration_sec=2.0)
            return False
        self.target = {name: self.measured[name] for name in names}
        return True

    def on_timer(self):
        joy = self.joy
        now = self.get_clock().now().nanoseconds * 1e-9

        if joy is None or now - self.joy_received_at > self.joy_timeout:
            if self.deadman_was_held:
                self.get_logger().warn("controller went silent, motion stopped")
            self.deadman_was_held = False
            return

        deadman_held = self.button(joy, self.deadman_button)
        if deadman_held and not self.deadman_was_held \
                and not self.seed_from_measured():
            return
        self.deadman_was_held = deadman_held
        if not deadman_held:
            return                  # controller holds its last point

        # Nominal dt, not measured wall time. The trajectory controller does
        # the real timing; a fixed step keeps the integration reproducible
        # regardless of how the Python timer jitters.
        for name in self.arm_joints:
            self.integrate(name, joy)
        self.publish(self.arm_publisher, self.arm_joints)

        if self.integrate(self.gripper_joint, joy):
            self.publish(self.gripper_publisher, [self.gripper_joint])

    def integrate(self, name, joy):
        """Advance one joint. Returns True if the stick actually asked for it."""
        entry = self.mapping[name]
        command = self.velocity_command(joy, entry)
        if command == 0.0:
            return False
        self.target[name] = clamp(
            self.target[name] + command * entry["scale"] * self.dt,
            entry["lower"], entry["upper"])
        return True

    def publish(self, publisher, names):
        point = JointTrajectoryPoint()
        point.positions = [float(self.target[name]) for name in names]
        point.time_from_start = Duration(
            seconds=self.lookahead * self.dt).to_msg()

        message = JointTrajectory()
        message.joint_names = names
        message.points = [point]
        publisher.publish(message)


def main():
    rclpy.init()
    node = RemoteControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Nothing is sent on the way out. The trajectory controller holds its
        # last point and the servos hold torque, which is the same contract
        # as robot_hardware's on_deactivate.
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()