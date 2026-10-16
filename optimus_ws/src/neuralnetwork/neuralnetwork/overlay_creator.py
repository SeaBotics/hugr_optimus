#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from foxglove_msgs.msg import ImageAnnotations, PointsAnnotation, TextAnnotation, Point2, Color


class OverlayNode(Node):
    def __init__(self):
        super().__init__('overlay_creator')

        # Subscribe to YOLO detection output
        self.subscription = self.create_subscription(
            Detection2DArray,
            '/oak/rgb/detections',
            self.detections_callback,
            10
        )

        # Publish Foxglove native 2D annotations
        self.publisher = self.create_publisher(
            ImageAnnotations,
            '/oak/rgb/image_annotations',
            10
        )

        self.get_logger().info("Overlay Node active. Listening on '/oak/rgb/detections'.")

    def detections_callback(self, msg: Detection2DArray):
        annotations = ImageAnnotations()

        if hasattr(annotations, 'timestamp'):
            annotations.timestamp = msg.header.stamp

        for detection in msg.detections:
            cx = detection.bbox.center.position.x
            cy = detection.bbox.center.position.y
            w = detection.bbox.size_x
            h = detection.bbox.size_y

            # Convert center-based coordinates to 4 box corners
            x1 = cx - (w / 2.0)
            y1 = cy - (h / 2.0)
            x2 = cx + (w / 2.0)
            y2 = cy + (h / 2.0)

            # Extract class ID / name
            class_name = ""
            score = 0.0
            if len(detection.results) > 0:
                hyp = detection.results[0]
                class_name = str(hyp.hypothesis.class_id).lower()
                score = hyp.hypothesis.score

            # --- Color Mapping Logic ---
            if 'green' in class_name:
                outline_color = Color(r=0.0, g=1.0, b=0.0, a=1.0)      # Bright Green
                fill_color = Color(r=0.0, g=1.0, b=0.0, a=0.2)         # Translucent Green
                label_bg_color = Color(r=0.0, g=0.5, b=0.0, a=0.8)     # Dark Green
            elif 'yellow' in class_name:
                outline_color = Color(r=1.0, g=1.0, b=0.0, a=1.0)      # Bright Yellow (R=1, G=1)
                fill_color = Color(r=1.0, g=1.0, b=0.0, a=0.2)         # Translucent Yellow
                label_bg_color = Color(r=0.5, g=0.5, b=0.0, a=0.8)     # Dark Yellow
            elif 'red' in class_name:
                outline_color = Color(r=1.0, g=0.0, b=0.0, a=1.0)      # Bright Red
                fill_color = Color(r=1.0, g=0.0, b=0.0, a=0.2)         # Translucent Red
                label_bg_color = Color(r=0.5, g=0.0, b=0.0, a=0.8)     # Dark Red
            else:
                # Default / Fallback color (Cyan)
                outline_color = Color(r=0.0, g=0.8, b=1.0, a=1.0)
                fill_color = Color(r=0.0, g=0.8, b=1.0, a=0.2)
                label_bg_color = Color(r=0.0, g=0.4, b=0.6, a=0.8)

            # 1. Bounding Box Outline (Closed Loop)
            box_anno = PointsAnnotation()
            box_anno.type = PointsAnnotation.LINE_LOOP
            box_anno.thickness = 2.0
            box_anno.outline_color = outline_color
            box_anno.fill_color = fill_color

            p1 = Point2(x=float(x1), y=float(y1))
            p2 = Point2(x=float(x2), y=float(y1))
            p3 = Point2(x=float(x2), y=float(y2))
            p4 = Point2(x=float(x1), y=float(y2))
            box_anno.points = [p1, p2, p3, p4]

            annotations.points.append(box_anno)

            # 2. Text Label
            if class_name:
                label_text = f"{detection.results[0].hypothesis.class_id} ({score:.2f})"

                text_anno = TextAnnotation()
                text_anno.position = Point2(x=float(x1), y=float(max(0.0, y1 - 5.0)))
                text_anno.text = label_text
                text_anno.font_size = 14.0
                text_anno.text_color = Color(r=1.0, g=1.0, b=1.0, a=1.0)  # White text
                text_anno.background_color = label_bg_color

                annotations.texts.append(text_anno)

        self.publisher.publish(annotations)


def main(args=None):
    rclpy.init(args=args)
    node = OverlayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
