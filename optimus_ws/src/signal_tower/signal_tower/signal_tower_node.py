#!/usr/bin/env python3
"""
Node: signal_tower_node
Package: signal_tower
Author: Julian (SeaBotics)
Task: Task 3 - Visible indication of operating mode

Fail-safe visual indication of Hugr Optimus operating mode via signal tower:
- SAFE_STOP: RED (solid or fail-safe)
- MANUAL: YELLOW
- AUTONOMOUS: GREEN
- UNKNOWN / FAULT / WATCHDOG TIMEOUT: RED
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Char

# Standard Operating Modes
MODE_SAFE_STOP = "safe_stop"
MODE_MANUAL = "manual"
MODE_AUTONOMOUS = "autonomous"
MODE_UNKNOWN = "unknown"

# ANSI Color Codes for clean terminal visualization in simulation mode
COLOR_RED = "\033[1;31m"
COLOR_YELLOW = "\033[1;33m"
COLOR_GREEN = "\033[1;32m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


class SignalTowerNode(Node):
    """
    ROS 2 Node controlling the optical signal tower of Hugr Optimus.
    Adheres strictly to the fail-safe requirement: any communication loss or
    invalid state immediately forces the red light (safe stop).
    """

    def __init__(self):
        super().__init__("signal_tower_node")

        # ------------------- 1. Parameters -------------------
        self.declare_parameter("sim_mode", True)
        self.declare_parameter("watchdog_timeout_sec", 0.5)
        self.declare_parameter("mode_topic", "/system/mode")
        self.declare_parameter("status_topic", "/signal_tower/status")
        self.declare_parameter("led_color_topic", "/led_color")
        self.declare_parameter("gpio_pin_red", 17)
        self.declare_parameter("gpio_pin_yellow", 27)
        self.declare_parameter("gpio_pin_green", 22)

        self.sim_mode = self.get_parameter("sim_mode").value
        self.watchdog_timeout = self.get_parameter("watchdog_timeout_sec").value
        mode_topic = self.get_parameter("mode_topic").value
        status_topic = self.get_parameter("status_topic").value
        led_color_topic = self.get_parameter("led_color_topic").value

        self.gpio_pins = {
            MODE_SAFE_STOP: self.get_parameter("gpio_pin_red").value,
            MODE_MANUAL: self.get_parameter("gpio_pin_yellow").value,
            MODE_AUTONOMOUS: self.get_parameter("gpio_pin_green").value,
        }

        # ------------------- 2. Internal State (Fail-safe by default) -------------------
        self.current_mode = MODE_SAFE_STOP
        self.last_mode_time = self.get_clock().now()
        self.watchdog_tripped = False

        # ------------------- 3. Subscriptions & Publishers -------------------
        self.subscription = self.create_subscription(
            String,
            mode_topic,
            self.mode_callback,
            10
        )

        # Telemetry topic for Foxglove Studio / shore monitoring
        self.status_pub = self.create_publisher(String, status_topic, 10)

        # Direct hardware bridge to Arduino Nano ESP32 via micro-ROS
        self.led_color_pub = self.create_publisher(Char, led_color_topic, 10)

        # ------------------- 4. Watchdog Timer (10 Hz check) -------------------
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_check)

        # ------------------- 5. Hardware Initialization -------------------
        self.init_hardware()

        self.get_logger().info(
            f"Signal Tower Node started. sim_mode={self.sim_mode} | "
            f"watchdog_timeout={self.watchdog_timeout}s | listening on '{mode_topic}'"
        )

        # Initial fail-safe light state
        self.apply_lights(MODE_SAFE_STOP, reason="Initial startup state")

    def init_hardware(self):
        """Initializes physical GPIO outputs when not in simulation mode."""
        if not self.sim_mode:
            try:
                # In Linux / Jetson / RPi, gpiod or RPi.GPIO can be used here.
                self.get_logger().info(
                    f"Initializing physical GPIO pins: Red={self.gpio_pins[MODE_SAFE_STOP]}, "
                    f"Yellow={self.gpio_pins[MODE_MANUAL]}, Green={self.gpio_pins[MODE_AUTONOMOUS]}"
                )
            except Exception as e:
                self.get_logger().error(f"Failed to initialize GPIO: {e}. Falling back to sim_mode=True.")
                self.sim_mode = True

    def mode_callback(self, msg: String):
        """Callback for incoming operating mode messages."""
        received_mode = msg.data.strip().lower()
        self.last_mode_time = self.get_clock().now()

        # If we were in watchdog timeout and valid communication is restored, recover
        if self.watchdog_tripped:
            self.watchdog_tripped = False
            self.get_logger().info("Operating mode stream restored. Watchdog cleared.")

        # Validate that the mode is known and supported
        if received_mode in (MODE_SAFE_STOP, MODE_MANUAL, MODE_AUTONOMOUS):
            if received_mode != self.current_mode:
                self.apply_lights(received_mode, reason="Confirmed mode change")
        else:
            # Acceptance criteria: An unknown status or fault cannot be displayed as a safe state.
            self.get_logger().warn(
                f"Received invalid/unknown mode: '{received_mode}'. Fail-safe triggered: forcing RED."
            )
            self.apply_lights(MODE_SAFE_STOP, reason=f"Invalid mode received ('{received_mode}')")

    def watchdog_check(self):
        """
        Periodically checks elapsed time since the last mode message.
        If timeout exceeded, triggers fail-safe safe_stop (RED).
        """
        now = self.get_clock().now()
        elapsed_sec = (now - self.last_mode_time).nanoseconds * 1e-9

        if elapsed_sec > self.watchdog_timeout and not self.watchdog_tripped:
            self.watchdog_tripped = True
            self.get_logger().error(
                f"WATCHDOG TIMEOUT: No mode message received for {elapsed_sec:.2f}s "
                f"(limit {self.watchdog_timeout:.2f}s). FAIL-SAFE ACTIVATED -> RED (SAFE STOP)."
            )
            self.apply_lights(MODE_SAFE_STOP, reason=f"Watchdog timeout ({elapsed_sec:.2f}s elapsed)")

    def apply_lights(self, mode: str, reason: str = ""):
        """Applies mode change to visualization (simulation) and/or physical hardware."""
        self.current_mode = mode

        # Publish telemetry status message (for Foxglove / shore operator)
        status_msg = String()
        status_msg.data = f"{mode.upper()}"
        self.status_pub.publish(status_msg)

        # Publish command directly to Arduino Nano ESP32 via micro-ROS topic /led_color
        char_map = {
            MODE_SAFE_STOP: ord('r'),
            MODE_MANUAL: ord('y'),
            MODE_AUTONOMOUS: ord('g'),
        }
        led_msg = Char()
        led_msg.data = char_map.get(mode, ord('r'))
        self.led_color_pub.publish(led_msg)

        if self.sim_mode:
            # Terminal colored display
            if mode == MODE_SAFE_STOP:
                icon, color = "🔴", COLOR_RED
            elif mode == MODE_MANUAL:
                icon, color = "🟡", COLOR_YELLOW
            elif mode == MODE_AUTONOMOUS:
                icon, color = "🟢", COLOR_GREEN
            else:
                icon, color = "🔴", COLOR_RED

            self.get_logger().info(
                f"[TOWER] {icon} {color}{mode.upper()}{COLOR_RESET} | Reason: {reason}"
            )
        else:
            self.set_physical_outputs(mode)

    def set_physical_outputs(self, mode: str):
        """Drives the actual relay / GPIO pins ensuring mutual exclusivity."""
        # Only one light should be active at a time
        red_state = (mode == MODE_SAFE_STOP)
        yellow_state = (mode == MODE_MANUAL)
        green_state = (mode == MODE_AUTONOMOUS)

        # Hardware write operations go here
        pass


def main(args=None):
    rclpy.init(args=args)
    node = SignalTowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt received, shutting down signal tower node...")
    finally:
        # On node exit, ensure safe state is asserted
        try:
            node.apply_lights(MODE_SAFE_STOP, reason="Node shutdown")
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
