# Manual control
I set up a manual control also, added a new package and used the joy to control the robotic arm.

The raspberry pi only reads radians from the URDF that moveit generates and translates to the servo angles. We can make the controller create these instead.

We make a package and a bringup, rpi5 is everything the same.
We use the "sudo apt install ros-jazzy-joy" package

# How we did it
1. Made a new package for the controller only, because rpi5 takes the radians from urdf and moveit2, we make a node that mimics this joint trajetcory planning and radians that the rpi5 translates to servo angles. (made it in python, joy is made in c++)
2. Download the joy library for ros2 on the rpi5 and testet and mapped the Xbox One controller we used
3.We had to also give permissions with: sudo usermod -aG input $USER -> exit -> login again -> groups | grep input and ros2 run joy joy_enumerate_devices -> This gave us the info we needed
4. We used the ros2 run joy game_controller_node to test it and echo with ros2 topic echo /joy

[INFO] [1786695872.085503691] [game_controller_node]: Controller Found: device_id=0, device_name=Xbox Series X Controller
[INFO] [1786695872.085766303] [game_controller_node]: Opened game controller: Xbox Series X Controller,  deadzone: 0.050000, rumble: Yes

Very simply the buttons give us value 0 or 1, so binary integer values, while the toggles between -1.0 and 1.0 floats or doubles idk something like that.

5. Made a config folder -> joystick_config.yaml
6. Made new node remote_control_node.py
7. made a launch folder -> remote_control.launch.xml
8. updates setup.py and package.xml

## How to use NOTE USE LAUNCH NOT RUN
Pi:      ros2 launch bringup robot_hardware.launch.xml
Laptop:  ros2 launch robot_bringup real_robot.launch.xml
Laptop:  ros2 launch robot_remote_control remote_control.launch.xml

Hold A when using sticks