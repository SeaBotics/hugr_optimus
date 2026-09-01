# robot_state_publisher: this node reads the URDF from /robot_description topic
# robot_state_publisher: subscribes to /joint_states topic published by a joint controller or joint_state_publisher (Virtual Data Generation)

# When you run robot_state_publisher, it automatically reads your URDF and broadcasts the static transform:
# base_link -> child_link

# Therefore (per now) no template code is used, only perhaps for more complex tasks.
