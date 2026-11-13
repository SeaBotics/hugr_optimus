# Lifecycle Nodes
Also called Managed nodes. NOT the same as Actions.

**WHY**
Useful initialisations
Order specific init
Easier reconfigurtions
Allocate resources and memory first (Real time OPS)
Synchronize node start ups for many nodes

Used for ros_control, NAV2 etc

**HOW**
Start/stop the camera, change parameters, like a state machine while Node runs

1. Starts Unconfigured, no com with hadrware
2. Transition
    on_configure (create ros2 topicm init hw com, calibrate etc) -> Hardware is ready
3. inactive
    on_activate (enable sensor)
4. active -> Publsihes sensor to topic
    on_deactive (opposite of on_activate)
5. also from inactive we could have on_cleanup where we stop HW and destroy ros2 topic

These are main states

6. on_shutdown (from any states)
    deactivates and cleanup
7. finalized