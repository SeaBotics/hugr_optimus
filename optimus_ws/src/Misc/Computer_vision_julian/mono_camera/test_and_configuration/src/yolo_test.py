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
        # Queue size 10 means buffer up to 10 messages 
        self.create_subscription(CompressedImage, "/image_raw/compressed", self.callback, 10)
        self.get_logger().info("Detector started, listening to /image_raw/compressed")  # Log startup message to terminal

    def callback(self, msg):                 # Callback function - runs every time CompressedImage message arrives
                                             # This runs ~30 times per second (your camera frame rate)
        self.frame_count += 1
        frame = self.bridge.compressed_imgmsg_to_cv2(msg)    # decompresses the ros2 compressed messages we have for YOLO
        self.get_logger().info(f"Frame {self.frame_count}: {frame.shape}")  # frame.shape prints dimensions [height, width, RGB Channels]

        results = self.model(frame, imgsz=320) # Our YOLO model with frame as the numpy array | also added image sizing to reduce uneccesairy size as YOLO upscaled earlier
        detections = results[0].boxes.data.cpu().numpy() # Firsy and only image in batch .boxes is the bbox .data is raw tensor .cpu move rom gpu to cpu (we dont have gpu in this setup therefore)
        # Result from detections is [x1, y1, x2, y2, confidence between 0 and 1, class_id]
        self.get_logger().info(f"Frame {self.frame_count}: Found {len(detections)} objects")

        cv2.namedWindow("yolo", cv2.WINDOW_NORMAL)
        cv2.imshow("yolo", results[0].plot())
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = Detector()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()