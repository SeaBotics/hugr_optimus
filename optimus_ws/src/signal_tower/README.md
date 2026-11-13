# signal_tower

Visual indication driver and fail-safe supervisor for the SeaBotics Hugr Optimus signal tower (Task 3).

## 1. What does the package do?
It manages the 3-state optical signal tower (Red, Yellow, Green) reflecting the confirmed operating mode of the autonomous vessel:
* 🔴 **Red (`safe_stop`)**: Safe stop, emergency stop (E-Stop), or disabled propulsion.
* 🟡 **Yellow (`manual`)**: Remote human teleoperation.
* 🟢 **Green (`autonomous`)**: Fully autonomous navigation.

### Fail-Safe & Watchdog
* **Default state on startup**: Always `safe_stop` (Red).
* **Unknown / Malformed input**: Immediately trips to `safe_stop` (Red).
* **Watchdog timer**: If communication with `/system/mode` drops for more than `watchdog_timeout_sec` (default 0.5s), the node automatically forces `safe_stop` (Red) and issues an alert.

## 2. Prerequisites and Dependencies
* **ROS 2**: Jazzy Jalisco (or Humble)
* **Packages**: `rclpy`, `std_msgs`
* **Python**: 3.10+

## 3. How do you install the package?
In the root of your ROS 2 workspace (`optimus_ws`):
```bash
cd ~/hugr_optimus/optimus_ws
rosdep install --from-paths src --ignore-src -y
```

## 4. How do you configure the package?
Configuration is handled in `config/signal_tower_params.yaml`:
```yaml
signal_tower_node:
  ros__parameters:
    sim_mode: true               # Set false on the physical boat to toggle GPIO/relays
    watchdog_timeout_sec: 0.5    # Max allowed latency before forcing fail-safe RED
    mode_topic: "/system/mode"   # Input mode topic from Task 2 (Operating Modes)
    status_topic: "/signal_tower/status" # Telemetry output for Foxglove
    gpio_pin_red: 17
    gpio_pin_yellow: 27
    gpio_pin_green: 22
```

## 5. How do you use the package?
### Launch the indicator node:
```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch signal_tower signal_tower.launch.py
```

### Verification with the built-in mock publisher:
Open another terminal:
```bash
source install/setup.bash
ros2 run signal_tower mock_mode_publisher
```
This will automatically cycle through all modes and simulate communication loss to demonstrate the fail-safe watchdog.

### Manual testing via CLI:
```bash
# Set Manual Mode (Yellow)
ros2 topic pub /system/mode std_msgs/msg/String "{data: 'manual'}" -1

# Set Autonomous Mode (Green)
ros2 topic pub /system/mode std_msgs/msg/String "{data: 'autonomous'}" -1

# Set Safe Stop (Red)
ros2 topic pub /system/mode std_msgs/msg/String "{data: 'safe_stop'}" -1
```

## 6. How do you run the tests?
```bash
colcon test --packages-select signal_tower
colcon test-result --verbose
```

## 7. How do you build, develop?
Always build from the workspace root:
```bash
colcon build --packages-select signal_tower --symlink-install
```

## 8. Maintainer
* Julian (SeaBotics Software Team)
* Email: idso.julianf@gmail.com
