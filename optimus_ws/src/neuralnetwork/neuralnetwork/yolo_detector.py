#!/usr/bin/env python3

from pathlib import Path
import cv2
import numpy as np
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import CompressedImage
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from ultralytics import YOLO


class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        # Automatically locate weights relative to this script's install path
        model_path = Path(__file__).parent / "YOLO26n_buoy_detector_v2.engine"

        if not model_path.exists():
            self.get_logger().error(f"Model file not found at: {model_path}")
            raise FileNotFoundError(f"Missing weight file: {model_path}")

        self.get_logger().info(f"Loading custom model from: {model_path}")
        self.model = YOLO(str(model_path))

        self.subscription = self.create_subscription(
            CompressedImage,
            '/oak/rgb/image_raw/compressed',
            self.image_callback,
            10
        )

        self.publisher = self.create_publisher(
            Detection2DArray,
            '/oak/rgb/detections',
            10
        )

        self.get_logger().info("Buoy Detector active and listening.")

    def image_callback(self, msg: CompressedImage):
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if cv_img is None:
                return

            results = self.model(cv_img, conf=0.5, verbose=False)

            detection_array = Detection2DArray()
            detection_array.header = msg.header

            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes.cpu().numpy()
                for box in boxes:
                    xywh = box.xywh[0]
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id] if hasattr(self.model, 'names') else str(class_id)

                    detection = Detection2D()
                    detection.header = msg.header

                    detection.bbox.center.position.x = float(xywh[0])
                    detection.bbox.center.position.y = float(xywh[1])
                    detection.bbox.size_x = float(xywh[2])
                    detection.bbox.size_y = float(xywh[3])

                    hypothesis = ObjectHypothesisWithPose()
                    hypothesis.hypothesis.class_id = str(class_name)
                    hypothesis.hypothesis.score = confidence

                    detection.results.append(hypothesis)
                    detection_array.detections.append(detection)

            self.publisher.publish(detection_array)

        except Exception as e:
            self.get_logger().error(f"Inference error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
