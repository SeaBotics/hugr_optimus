# Important about this package
Last Revision: Julian F idsoe / 19/08/2026
Status: Under Development

About Data and Interfaces:
It uses: `from geometry_msgs.msg import PointStamped`
The data in are 6 values -> Out we publish x,y,z
The z = 0 for this application always.
The x,y are the centroid of the object, and are given with float.

Dependencies outside Rosdep:
opencv-python
ultralytics

Note: 
When running topic echo or topic hz there may be nothing before an object, i.e bottle, is in the camera peripherals, When an object is detected data is sent.

There are 3 places in code marked, where the cv2 is commented out. Remove the comment if you need to visualize the tracking algorithm for debugging.
Else it is commented out and the code runs fine.

TODO: There is not a TF set up, therefore no relatvity to objects.