# ROS2 Nodes
The code that does something liek a camera node

Nodes should be limited to a single process for good practice to be modular.
Example -> Camera package -> Have different nodes for camera feed, camera processing etc

A node may read sensor data -> Publish data -> Another node subscribes and process the data
The nodes are combined into something called a "graph".

They communicate through topics, services and parameters.

I therefore personally believe in:
- Define "What do we want the system to do" on a high level -> Our workspace
- Define what parts should we divide the system into -> Our packages
- Then make the processes -> Our nodes 

With this architcture we have a modular defined system.
Also as ros2 has the python and c++ as main languages, python = rapid prototyping, c++ = fast actor.

Nodes names are unique, no nodes may share a name.
