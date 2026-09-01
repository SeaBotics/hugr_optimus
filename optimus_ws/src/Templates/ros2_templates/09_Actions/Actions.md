# Actions in ROS2
Used for alot like NAV2, ROS_Control and MoveIt

## Backgroud and comparison
We know ros2 has communication stools like topics (pub/sub to end data). Not aware o each other. ROS Services (client/server communications).

Example for use/not use
- Topics
It is not UDP, but think of it ~UDP with unidirectional, asynchronous (BEST EFFORT)

Use: Send data, where msg's are not problematic to loose, like reading a sensor IMU.
Non-use: Critical commands with stamps and synchronous requests, like start calibration, we cant loose the msg

- Services
It is not TCP, but think of it like ~TCP with synchronous, two-way request/response with asnwer.

Use: Discrete, state-machines,  immediate, success/failure, like Getting a battery state og set a state, A then B.
Non-use: streaming data, makes bottlenecks.

### Actions (Event with feedback)
An action may take some time, execution takes time.
Allows us to quit mid request and gives us updates underway.
Handling multiple client requests and choosing or refuse.

We use Action Client and Action Server.

1. We have a action server, where we can send a request (Send Goal).
2. We either get accepted or rejected by the action server
3. If accepted, action server process our Goal.
4. Client receives notification. ¨
5. Feedback can be sent underways, f.eks position x,y at time t, and position x2,y2 at time t2.
6. We have a response code we can quit the Goal underways, or send new Goal, or do an intermediate Goal.


Example from a course:
**Action Client**
Send Goal -> Move to (x,y)
<- Goal Accepted or Rejected
Cancel Goal Requst ->
<- Response Code
<- Feedback
<- Goal Status
Request Result (if goal accepted) ->
<- Result
**Action Server**

Cancel and Feedback is optional.
Topics and Services in the Action follow our template on this.

Many Actions Clients, only one Action Server (Decide what to do with Goals)

### Create package
Same way as usual with ros2 pkg create name without any dependencies this time
Gives us the CMakeLists.txt, package.xml **but important** add: mkdir (For complete use, may not be neccesairy)
1. action
2. msg <- Used in topics
3. srv < - Used in service

#### Making an action (in action folder)
1. MyAction.action (Camelcase) and use a verb
See the template we have
In serice we have the Request and response seperated with a --- , but action also have --- feedback

2. In the package.xml
add the mandatory rosidl_default_generators <- Buildtool>
add exec depend -> default runtime
add memeber of group rosidl_interface_packages

3. Cmakelists.txt
Add in find packages
rosidl default generators botht he find package and project name and ament dependencies
Add in project name "action/actionname.action" after this below add for defintiions like msg srv etc

4. ros2 interface show -> See our action interface (Must be done)

## More in depth
One of the strong points of actins Accept or Reject a goal

**We use Goal State Machine as a very important part** Not confuse with Behaviour Trees in ROS2 (not the same)
1. send_goal (accepted)
2. Accepted
3. execute -> Executing
    while executing we can cancel -> then either succeed if close enough or abort if not satisfying
4. if succeed -> Succeded
4. if abort -> Aborted

Other ways would we paralell goals, refusing new goals or queue them, or even change priority and order (State machines).

