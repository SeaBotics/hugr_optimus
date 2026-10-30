# TestingLights

Firmware for the Arduino Nano ESP32 used to test the Optimus LED signal and motor outputs. The board runs an Arduino-based micro-ROS node and communicates with a ROS 2 system through the native USB serial connection.

## What does this package do?

The firmware creates the `esp32_nano_node` micro-ROS node and subscribes to:

| Topic | Message type | Accepted values |
| --- | --- | --- |
| `/led_color` | `std_msgs/msg/Char` | `o` off, `r` red, `g` green, `y` yellow |
| `/motor_pwms` | `std_msgs/msg/Int32MultiArray` | Four PWM values in microseconds |

TODO, the off has to be fixed, as the "off" turns LOW the pin triggering the relays off, therefore, sending 'o' shuts down the motors.
And of course, to have the light off, just put on low all the pins related to the lights (LOW=6,7,8)

LED commands select one signal output. Unknown LED commands default to red. Motor commands are applied only when the message contains at least four values; each value is limited to `1100`-`1900` microseconds. Motors start at the stop value of `1500` microseconds.

### Hardware mapping

| Function | GPIO |
| --- | ---: |
| Rele Pin | 6 |
| Green LED | 7 |
| Yellow LED | 8 |
| Red LED | 9 |
| Motor 1 | 3 |
| Motor 2 | 4 |
| Motor 3 | 11 |
| Motor 4 | 12 |

The board waits approximately 3.5 seconds during startup after initializing the motor outputs.

## Prerequisites and dependencies

- Arduino Nano ESP32 hardware and USB cable
- PlatformIO Core or the PlatformIO extension for VS Code
- A ROS 2 Jazzy installation with a micro-ROS agent available on the host computer
- USB access permissions for the serial device on Linux
- The LED and motor hardware connected according to the mapping above (plz read the fine manual from electronics dept for pinouts)

PlatformIO resolves the project dependencies from `platformio.ini`:

- Arduino framework for the `arduino_nano_esp32` board
- `ESP32Servo` version `3.0.5` or compatible `3.x` version
- `micro_ros_platformio` with the Jazzy micro-ROS distribution

## Installation

Clone the repository and open this directory as the PlatformIO project:

```bash
git clone <repository-url>
cd hugr_optimus/ESP32NanoFirmware/TestingLights
```

PlatformIO downloads the declared libraries automatically during the first build. No separate package installation is required.

## Configuration

Project configuration is in [`platformio.ini`](platformio.ini). It defines the Arduino Nano ESP32 board, Arduino framework, micro-ROS Jazzy distribution, USB CDC settings, and serial monitor speed of `115200` baud.

Before using the firmware:

1. Connect the LEDs and motor controllers to the GPIO pins listed above.
2. Confirm that the connected motor controllers accept the `1100`-`1900` microsecond range. (Just in case ESCs are different from originals)
3. Connect the board over its native USB port.
4. If the serial device is not accessible on Linux, add the user to the appropriate device group or configure a udev rule.

## Build, upload, and monitor

Run these commands from `ESP32NanoFirmware/TestingLights`:

```bash
pio run                 # Build the firmware
pio run -t upload       # Build and upload to the board
pio device monitor      # Open the 115200-baud serial monitor
```

If PlatformIO does not select the correct serial port automatically, list available ports and pass one explicitly:

```bash
pio device list
pio run -t upload --upload-port /dev/ttyACM0
pio device monitor --port /dev/ttyACM0 --baud 115200
```

The serial output includes startup messages such as `Setup complete. Waiting for messages...`.

## Usage

Start a micro-ROS agent on the host using the serial device connected to the board. The exact command depends on the installed agent transport; for example:

```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 115200
```

After the agent connects, publish test commands from another ROS 2 terminal:

```bash
# Turn on the green LED
ros2 topic pub --once /led_color std_msgs/msg/Char "{data: 'g'}"

# Set all four motor outputs to the stop value
ros2 topic pub --once /motor_pwms std_msgs/msg/Int32MultiArray \
  "{data: [1500, 1500, 1500, 1500]}"
```

The motor callback ignores arrays with fewer than four entries. Test motor outputs with the propellers or other hazardous loads disconnected first.

## Tests

The project currently has no implemented PlatformIO tests; the `test/` directory contains the default PlatformIO documentation only. The test command is:

```bash
pio test
```

Until hardware or unit tests are added, validate changes by building, uploading to a board, checking the serial monitor, and publishing both ROS 2 topics through a micro-ROS agent.

## Development

Edit the firmware in [`src/main.cpp`](src/main.cpp). Keep hardware constants and topic contracts synchronized with the ROS 2 nodes that publish to this board. Build after code changes with:

```bash
pio run
```

For iterative development, use the PlatformIO VS Code extension to build, upload, and monitor the board. Changes to the motor or LED wiring must also be reflected in the pin definitions and this README.

## Maintainer

Maintained by the SeaBotics Student Association at the University of Agder. See the repository's contribution guidance in the root [`README.md`](../../README.md).
