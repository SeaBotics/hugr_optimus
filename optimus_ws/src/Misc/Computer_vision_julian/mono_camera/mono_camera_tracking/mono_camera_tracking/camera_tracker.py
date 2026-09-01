#!/usr/bin/env python3
# Note ty myself, "self" is used a lot in ros2, it is "The thing im inside right now" this object
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from ultralytics import YOLO
from cv_bridge import CvBridge            # Converts ROS image messages <-> OpenCV format (Numpy array)
import cv2                                # We use for the imshow and waitkey for visualization of the camera, and debug D and R.
from geometry_msgs.msg import PointStamped

class Detector(Node):
    def __init__(self):
        super().__init__("centroid_tracker")

        self.frame_count = 0
        self.model = YOLO("yolov8n.pt") 
        self.bridge = CvBridge()          # Creates a converter object

        # Create subscriber: listen to /image_raw/compressed topic
        # When message arrives, run self.callback function automatically
        # Queue size n means buffer up to n messages 
        self.create_subscription(CompressedImage, "/image_raw/compressed", self.callback, 10)
        self.get_logger().info("Detector started, listening to /image_raw/compressed, not detecting? Check if you publish or if topic name is correct")  # Log startup message to terminal

        # Tracking is about comparing last and new frames, callbacks only live now, therefore we must implement something to keep it
        # We must attach it to the node object not the function
        # Using None the variable exist but has no value yet
        self.locked_x = None 
        self.locked_y = None 
        # Data is: 2 values-> x,y coordinates, type Float

        self.max_jump = 80 # This is limit we set to reject if the object is too far away to probably be our object if it jumps, must be calibrated

        # We publish our x,y coordinate to the centroid, so other applications can use just that x,y value without concern for the rest
        # This is to allow to be used i.e robotic arm or car to follow or mimick.
        self.publisher = self.create_publisher(PointStamped, "/centroid_tracker", 10)
    

    def callback(self, msg):                 # Callback function - runs every time CompressedImage message arrives
                                             # This runs ~30 times per second (our camera frame rate at the moment)
        self.frame_count += 1
        frame = self.bridge.compressed_imgmsg_to_cv2(msg)    # decompresses the ros2 compressed messages we have for YOLO
        self.get_logger().info(f"Frame {self.frame_count}: {frame.shape}")  # frame.shape prints dimensions [height, width, RGB Channels]

        results = self.model(frame, imgsz=320, classes=[39]) # Added the classes=[model], 39 is bottle in Common Object in Contect (COCO) 80x different in yolov8n
        detections = results[0].boxes.data.cpu().numpy() # First and only image in batch .boxes is the bbox .data is raw tensor .cpu move rom gpu to cpu (we dont have gpu in this setup therefore)

        # detections is 2D array
        # Below is just for gui, remove comments when using gui for troubleshooting like seeing what the camera sees
        # annotated = results[0].plot() # This is for a centroid circkle just visual

        best_x, best_y, best_distance = None, None, 1e9 # Where we store our last known target values, known as best value estimation

        # Note that there is always 6 columns in pr row there for a _ is a placeholder in the detections for loop
        for x1, y1, x2, y2, confidence, _ in detections:
            cx, cy = (x1 + x2) /2 , (y1+y2)/2     # We defined cx and cy so we have the data to use later when tracking or anything

            if self.locked_x is None:
                distance = 0
            else:
                distance = ((cx - self.locked_x)**2 + (cy - self.locked_y)**2)**0.5
            # We have the first lock just be None as it does not exist yet, then when we get the frames we use pythagorean theroem to find the distance between
            # This is because we get a value to compare with that is the only way we can test and compare

            if distance < best_distance and distance < self.max_jump:
                best_x, best_y, best_distance = cx, cy, distance
            # If the candidate is closest its the new best or lock we use, also added the max_jump to try to limit the sudden movement of the bbox

        if best_x is not None:
            self.locked_x, self.locked_y = best_x, best_y

            # Below is just for gui, remove comments when using gui for troubleshooting like seeing what the camera sees
            # cv2.circle(annotated, (int(best_x), int(best_y)), 4, (0,0,255), -1) # 4 is radius, change it if needed | BGR is used not RGB | -1 is solid fill, 1 is outline 1 pixel, 2 is 2 pixel etc
            
            self.get_logger().info(f"lock ({best_x:.0f}, {best_y:.0f})")

            # The x,y values of the tracker is published with the code below
            point = PointStamped()
            point.header.stamp = self.get_clock().now().to_msg()
            point.point.x, point.point.y = float(self.locked_x), float(self.locked_y)
            self.publisher.publish(point)
            # Note a TF frame is not added, TODO: point.header.frame_id = "our camera" 

        # Result from detections is [x1, y1, x2, y2, confidence between 0 and 1, class_id]
        self.get_logger().info(f"Frame {self.frame_count}: Found {len(detections)} objects")

        # Below is just for gui, remove comments when using gui for troubleshooting like seeing what the camera sees
        # cv2.namedWindow("yolo", cv2.WINDOW_NORMAL) # Creates a reshapable window
        # cv2.imshow("yolo", annotated) # Made it so instead of bbox we use the centroid as a marker note before we used only results[0].plot()
        # cv2.waitKey(1)                # Just waits 1ms on keyboard input


def main(args=None):
    rclpy.init(args=args)
    node = Detector()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()