# Parameters for ROS2
Used to tweak and adjust settings in code.
- ports
- fps
- speed
etc etc alot more

No need to build or compile.

Using

self.declare_parameter("number", 2) > example, the datatypes is given now 2, not 2.0 or "2".
self.number_ = self.get_parameter("number").value 
self-timer_period 
declare then get it, save in attribute. 

# YAML Files (.yaml)
Really clever for tuning, and altering

# Tips
Also when running an application, the .yaml file can be changed and saved, and run those changes in terminal by:
`ros2 param load /complete_node_name path/to/your_file.yaml`

or one could use: 
`ros2 run rqt_reconfigure rqt_reconfigure`

# Parameters Callback
from rclpy.paramater import Parameter