#!/usr/bin/env python3
# Note ty myself, "self" is used a lot in ros2, it is "The thing im inside right now" this object
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from ultralytics import YOLO
from cv_bridge import CvBridge            # Converts ROS image messages <-> OpenCV format (Numpy array)
import cv2                                # We use for the imshow and waitkey for visualization of the camera, and debug D and R.

class Detector(Node):
    def __init__(self):
        super().__init__("detector")

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
    

    def callback(self, msg):                 # Callback function - runs every time CompressedImage message arrives
                                             # This runs ~30 times per second (our camera frame rate at the moment)
        self.frame_count += 1
        frame = self.bridge.compressed_imgmsg_to_cv2(msg)    # decompresses the ros2 compressed messages we have for YOLO
        self.get_logger().info(f"Frame {self.frame_count}: {frame.shape}")  # frame.shape prints dimensions [height, width, RGB Channels]

        results = self.model(frame, imgsz=320, classes=[39]) # Added the classes=[model], 39 is bottle in Common Object in Contect (COCO) 80x different in yolov8n
        detections = results[0].boxes.data.cpu().numpy() # First and only image in batch .boxes is the bbox .data is raw tensor .cpu move rom gpu to cpu (we dont have gpu in this setup therefore)

        # detections is 2D array
        annotated = results[0].plot() # This is for a centroid circkle just visual

        # Note that there is always 6 columns in pr row there for a _ is a placeholder in the detections for loop
        for x1, y1, x2, y2, confidence, _ in detections:
            cx, cy = (x1 + x2) /2 , (y1+y2)/2     # We defined cx and cy so we have the data to use later when tracking or anything
            self.get_logger().info(f"bottle ({cx:.0f}, {cy:.0f}) {confidence :.2f}")
            cv2.circle(annotated, (int(cx), int(cy)), 4, (0,0,255), -1) # 4 is radius, change it if needed | BGR is used not RGB | -1 is solid fill, 1 is outline 1 pixel, 2 is 2 pixel etc

        # Result from detections is [x1, y1, x2, y2, confidence between 0 and 1, class_id]
        self.get_logger().info(f"Frame {self.frame_count}: Found {len(detections)} objects")

        # Below is just for gui, does not produce any data we actively use
        cv2.namedWindow("yolo", cv2.WINDOW_NORMAL) # Creates a reshapable window
        cv2.imshow("yolo", annotated) # Made it so instead of bbox we use the centroid as a marker note before we used only results[0].plot()
        cv2.waitKey(1)                # Just waits 1ms on keyboard input


def main(args=None):
    rclpy.init(args=args)
    node = Detector()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()