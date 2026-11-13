# thrust_allocation package

Takes input via the joystick_drivers submodule to take inputs from a xbox/ps5 controller which allocates the kinematics of optimus and outputs a PWM signal mapped to the Basic ESC Controllers.

## How to use the package

To use thrust_allocation package (check [Dependencies](#dependencies) if errors).

1. Source your terminal

```bash
source /opt/ros/jazzy/setup.bash
```

2. Colcon Build the package within `/optimus_ws/src`

```bash
colcon build --packages-select thrust_allocation
```

3. Source the workspace

```bash
source /install/setup.bash
```

4. In the second terminal run joy_node (remember to source this terminal as well).

```bash
ros2 run joy joy_node
```

5. Final step, launch the thrust_allocation package!

```bash
ros2 launch thrust_allocation thrust_allocation.launch.xml
```

## Dependencies

thrust_allocation is dependent on specific packages. To install these, simply use the rosdep tool.

1. Initializing rosdep and updating it

```bash
sudo rosdep init
rosdep update
```

2. Actually installing the different dependencies in package. Do this in `optimus_ws/src`

```bash
rosdep install --from-paths src -y --ignore-src
```

## How to alter the package

All of these parameters are freely able to be changed. Simply change the values accordingly (use "." for decimals).

`thruster_params.yaml`

```yaml
    mass: 3.0       # kg
    d1x: 0.35       # metre
    d1y: 0.35
    d2x: 0.35
    d2y: 0.35
    d3x: 0.35
    d3y: 0.35
    m1: 0           # metre
    m2: 0
    m3: 0
    deadzone: 0.05  # controller

```

`thruster_allocation_node`

```cpp
---

// free to change the integer before ms (publish frequency)
    timer_ = this->create_wall_timer(20ms, timer_callback);

---

// You can change the deadzone value within the joystickCommand function
void joystickCommands()
    deadzone_ = 0.05;

---
```

## Example

| Max values | Left Joystick (x) | Left Joystick (y) | Right Joystick (\tau) |
| :------: | :----------:| :----------: | :----------: |
| + |  1.0 | 1.0 | 1.0 |
| neutral |  0.0 | 0.0 | 0.0 |
| - | -1.0 |-1.0 |-1.0 |

## Code deep dive

This code uses `this->declare_parameter("name", value);` to declare an variable just-in-case if the YAML (config) might not get found/lost.

Otherwise, if the YAML file IS found, private members with _ behind their name will get their value from the config file.

```cpp
/ Parametres
        // Hull
        this->declare_parameter("mass", rclcpp::PARAMETER_DOUBLE);
        this->declare_parameter("d1x", 0.35);
        this->declare_parameter("d1y", 0.35);
        this->declare_parameter("d2x", 0.35);
        this->declare_parameter("d2y", 0.35);
        this->declare_parameter("d3x", 0.35);
        this->declare_parameter("d3y", 0.35);
        this->declare_parameter("deadzone", 0.05);

        mass_ = this->get_parameter("mass").as_double();
        d1x_  = this->get_parameter("d1x").as_double();
        d1y_  = this->get_parameter("d1y").as_double();
        d2x_  = this->get_parameter("d2x").as_double();
        d2y_  = this->get_parameter("d2y").as_double();
        d3x_  = this->get_parameter("d3x").as_double();
        d3y_  = this->get_parameter("d3y").as_double();
        
        // Controller
        deadzone_ = this->get_parameter("deadzone").as_double();

```

Subscribing to the topic `/joy` with QoL: 10, and using std::bind() with ThrustAllocationNode::joystickCommands function which gathers the different axes from the joy_node.

```cpp
// Recieve joy
        subscriber_ = create_subscription<sensor_msgs::msg::Joy> (
            "/joy", 10,
            std::bind(&ThrustAllocationNode::joystickCommands, this, _1));

```

joystickCommands function within the std::bind() function which lets the members Fx_, Fy_, and tau_ listen to the topic /joy whilst also checks for deadzone for all axis

| input | index | axis |
|:--------:|:----------:|:-----------:|
| Fy_ | 0 | Left/Right Axis stick left |
| Fx_ | 1 | Up/Down Axis stick left |
| tau_ | 3 | Left/Right Axis stick right |

```cpp
// Interpret sticks
    void joystickCommands(const sensor_msgs::msg::Joy::ConstSharedPtr msg){
        // Initializing declarations
        Fx_  = msg->axes.at(1);
        Fy_  = -msg->axes.at(0);
        tau_ = -msg->axes.at(3);
        deadzone_ = 0.05;
        // Simple deadzone logic
        if(abs(Fx_)  <= deadzone_)
            Fx_ = 0;
        if(abs(Fy_)  <= deadzone_)
            Fy_ = 0;
        if(abs(tau_) <= deadzone_)
            tau_ = 0;
    }
```

Publishing a topic `/thrust_alocation` with message type Vector3() which packs `Fx_, Fy_, tau_`. and the private `timer_` member publishes the data every 20ms to the topic

```cpp
// Publish
        publisher_ = create_publisher<geometry_msgs::msg::Vector3>(
            "thrust_allocation", 10);
        
        auto timer_callback =
        [this]() -> void {
            auto message = geometry_msgs::msg::Vector3();
            message.x = Fx_;
            message.y = Fy_;
            message.z = tau_;
            RCLCPP_INFO(this->get_logger(),
            "Publishing: '%.2lf', '%.2lf', '%.2lf'",
            message.x, message.y, message.z);
            this->publisher_->publish(message);
        };
        timer_ = this->create_wall_timer(20ms, timer_callback);
```

Main uses a shared pointer for the `ThrustAllocationNode` which is sent to spin() indefinitly until manually stopped with "Ctrl + C" and shut down with `rclcpp::shutdown()`

```cpp
int main(int argc, char* argv[]){
    rclcpp::init(argc, argv);
    auto node = std::make_shared<ThrustAllocationNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
```

> Maintained by SeaBotics Student Association
