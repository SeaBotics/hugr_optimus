**Note** Utilizing the Turtlebot3 for testing urdf, xacro and Gazebo is hugly reccomended. Similar to turtlesim (2D) but 3D.
https://github.com/ROBOTIS-GIT/turtlebot3_simulations and also check NAV2: https://docs.nav2.org/tutorials/docs/navigation2_on_real_turtlebot3.html

Github: https://github.com/gazebosim/gz-sim/tree/gz-sim9

Tips, for existing projects where ros2 and gazebo run with eachother, see how they set it up.

# How to set up an Environment
- gz sim
- gz topic -l <- lists the topics
- ros2 topic lists does not give it therefore add a brigde for this
- Theres a percentage in bottom right, that gives % of 100 of seconds ran.

## Launch Gazebo

- Start -> `ros2 launch ros_gz_sim gz_sim.launch.py gz_args:=empty.sdf`
- or use -> `ros2 launch ros_gz_sim gz_sim.launch.py rviz:=true`

## Bridging ROS2 and Gazebo
`ros_gz_bridge` package

To illustarte the point gazebo could publish the `joint_states` and that would be dispalyed in ros2 as if it was real.
Plugin: Joint state publisher

### Inertial tags must be applied for gazebo for each rigid body. NO inertial tag == no physics appaer in Gazebo (Gazebo use mass moment of Inertia Kg * m^2)

 - I would reccomend a robotics or mechanical engineering book to calculate Inertia for Gazebo.
 - If using a CAD software like i do (Onshape or SolidWorks) these can caluclate the 3x3 inertia matrix also. Make sure inertia is taken about CoM, or else Steiner formutheorem must be applied (Not reccomended, easy to make mistake)

 - else this link from wikipedia is OK: https://en.wikipedia.org/wiki/List_of_moments_of_inertia

 To simplify we can use inertia and mass values as more simple functions rather than the complex visual CAD model.

 ### Collision tags must be applied in gazebo for crashing and stuff
`<collision>` used, simplify the physics with a box, instead of high polgygon meshes. Keep the visual like the CAD model.
Try to match the external xyz of the visual soa crash is detected and for collision avoidance.

**Note**
Tips for collision with wheels, do not use cylinder. Better to use sphere. The cylinder may slow down the robot. Sphere gives only one point of collision.
`<geometry><sphere radius>` etc. Collision with baselink that is static is not a problem (Only moving arms like a manipulator)

#### Tip for strcuture
1. Visual
2. Collision
3. Inertial

Use this order, then you have a strcuture, it does noe affect anything but the .xml file is long anf big, easier to keep track.
You can make a comment in .xml for the uRDF like: `<!-- Comment -->`

## Spawn robot in Gazebo
1. terminal -> start `robot_state_pulisher` with --ros-args -p robot_description:="$(xacro filename)" -> returns Robot initialized
2. terminal -> start `ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="empty.sdf -r"` -> r starts the time not neccesairy can be done in gazebo
3. terminal -> start `ros2 run ros_gz_sim create -topic robot_description` -> starts a node that uses our URDF (Spawn robot)
4. terminal -> start `ros2 run rviz2 rviz2 -d ros2/ws/src/my_robot_description/rviz/urdf_config.rviz` to introspect the tf2 and check that ros2 and gazebo exist together.


## Adding the plugin for control in Gazebo
Add plug-ins so we get `/joint_states` for control in gazebo and ros2, and get the tf2 up and running.
`ros2 topic echo /joint_states`
`rqt_graph`

system and plug-in are used with each other
**NB** - Plugins using .cc or .hh files

**NB** - https://github.com/gazebosim/gz-sim/tree/main/src/systems
Theres a name in the cc file also must be used in th e.xml file

Odom to base TF is important. This lets the robot start in a origin, and track the movement from the start (Odometry). /odom is important for NAV2 also.
Using a base_footprint as a projection of the base_link to the floor, and have odometry from that.

There is also another plugin: joint_state_publisher from gazebo, that simulates the hardware.
`<plugin filename=">`and `<name=>`

**NB** - https://github.com/gazebosim/gz-sim/tree/main/src/systems/joint_state_publisher

 `<gazebo reference>`allows to add friction coefficients with the wheel and ground or other. -> `<mu1>` coloumb fricition.
 A passive joint in Gazebo is a joint that is not actuated (it does not have a motor, PID controller, or transmission linked to it). It moves freely solely in response to external forces, gravity, or mechanical constraints from other moving parts (e.g., a caster wheel, a spring-loaded gripper, or a passive joint in a parallel closed-loop mechanism like a four-bar linkage).

## Set up Gazebo bridge
Docs: https://github.com/gazebosim/ros_gz/tree/ros2/ros_gz_bridge
 or
https://github.com/gazebosim/ros_gz
https://gazebosim.org/docs/latest/ros2_integration/

Start a `<node pkg="ros_gz_bridge" exec="parameter_bridge">`
you can make a config folder in the launch folder 
- make a gazebo_bridge.yaml -> Create bridge for each topic

#### topic 1
- ros_topic_name: "
gz_topic_name: ""
ros_type_name: ""
gz_type_name: ""
direction: 

#### topic 2 etc
- ros_topic_name: "
gz_topic_name: ""
ros_type_name: ""
gz_type_name: ""
direction: 

We must access the gazebo clock /clock -> may call it /clock, gz and ros2 types -> `gz topic -i -t <topic name>`

direction: GZ_TO_ROS    ROS_TO_GZ   BIDIRECTIONAL <- use these for pub or sub

### Debugging
Note Gazebo topics wont show in rqt_graph, but you can see /ros_gz_bridge running in to joint_states
Using teleop twist keyboard is good

## Create a world in Gazebo
Before making your own check -> resource spawner in top right
https://app.gazebosim.org/fuel/models

Add mesh in entity tree for external files
textures if model lack color in your path

**NB**
Save the world
- Remove your robot
- Save world as -> .sdf
- Close gazebo

### Launch robot in the world
Make a folder worlds in the bringup package
- add it to the cmakelists install
copy the .sdf in this folder

Troubleshooting: sometimes models are not in corret path

## Add a Sensor
added in the .sdf xml file

### From tutorial adding a camera
1. Add the sensor in the urdf
2. Do not make it flush as sensor ma be obscured by the 3d models
3. add the plugin -> https://github.com/gazebosim/gz-sensors/tree/main
4. add the `<plugin>`then `<render_engine>`. "ogre_2" maybe.
5. `<sensor>` aftwerards fov, `<optical>`, type gaussian, etc must be added. `<update rate>`.
6. Note, it seems as the data will represent what is described, may be very hard to simulate a real sensor than optimal, but still better than nothing. -> test collision avoidance, imu filters, camera object detetction etc. For example: Algoritm detects yellow box, simulate this box with ideal (may add gaussian noise) train model, refine in the real world.
7. OpenCv -> diferent axis convention -> OpenCv use z in front, ros2  use x. -> https://robotics.stackexchange.com/questions/73459/gazebo-camera-frame-is-inconsistent-with-rviz-opencv-convention




## Tips xacro
you can create multiple urdf files, and include them in a final xacro file for modularity

### TIPS FOR ROS2 MAVLINK 
**NOTE; I found that Micro-XRCE does not pr (21/7/26) support this for Sub only copter and rover it seems**
https://github.com/eProsima/Micro-XRCE-DDS-Agent <- say goodbye to MAVROS
https://docs.px4.io/main/en/middleware/uxrce_dds <- From PX4

I belive that Micro-XRCE (AP_DDS) is maybe faster or have less overhead.

# I will therefore link MAVROS as a one folder, but setp still applies:
