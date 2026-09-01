# Add the dependencies in package.xml for our interfaces
# Use the server template but add these points
# Important if using AI, it seasy t feel their code is better with much code and libs but follow this rule
# As little code as possible for simplicity

from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle # for server or client for client
from my_custom_interface.action import theinterface

# We start with getting request from Goal
# We must have the client create, then send the goal to the server
# Use send_goal_asyc as normal may give problem with rclspin

# With terminals we  see:

# Terminal 1: Action server has been started
# Terminal 2: Sending Goal
# Terminal 1: Execution the goal ... | Terminal 2: Goal Was accepted/rejected -> accepted would continoue with feedback


# We use callbaskcs and future 's

# One of the strong points of actins Accept or Reject a goal
# we must validate the request (that the msg/srv data type is allowed) like if only ints, -1 is illegal. Can set ACCEPT or REJECT

