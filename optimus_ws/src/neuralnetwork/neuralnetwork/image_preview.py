#!/usr/bin/env python3

import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, CompressedImage


def scale_camera_info(info, header, width, height):
    sx = width / info.width
    sy = height / info.height
    out = CameraInfo()
    out.header = header
    out.width = width
    out.height = height
    out.distortion_model = info.distortion_model
    out.d = info.d
    out.r = info.r
    k = list(info.k)
    k[0] *= sx
    k[2] *= sx
    k[4] *= sy
    k[5] *= sy
    out.k = k
    p = list(info.p)
    p[0] *= sx
    p[2] *= sx
    p[3] *= sx
    p[5] *= sy
    p[6] *= sy
    out.p = p
    return out


class Stream:
    def __init__(self, node, name):
        self.node = node
        self.info = None
        self.next_time = 0.0
        base = f'/oak/{name}'
        self.image_pub = node.create_publisher(CompressedImage, f'{base}/preview/compressed', 1)
        self.info_pub = node.create_publisher(CameraInfo, f'{base}/preview/camera_info', 1)
        node.create_subscription(
            CameraInfo, f'{base}/camera_info', self.on_info, qos_profile_sensor_data)
        node.create_subscription(
            CompressedImage, f'{base}/image_raw/compressed', self.on_image, qos_profile_sensor_data)

    def on_info(self, msg):
        self.info = msg

    def on_image(self, msg):
        now = time.monotonic()
        if now < self.next_time:
            return
        # Accumulate the period so 30 fps input averages out to max_fps, not every other frame
        self.next_time = max(self.next_time + self.node.period, now)

        img = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return
        width = self.node.get_parameter('width').value
        height = self.node.get_parameter('height').value
        quality = self.node.get_parameter('jpeg_quality').value
        small = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            return

        out = CompressedImage()
        out.header = msg.header
        out.format = 'jpeg'
        out.data = buf.tobytes()
        self.image_pub.publish(out)

        if self.info is not None and self.info.width and self.info.height:
            self.info_pub.publish(scale_camera_info(self.info, msg.header, width, height))


class ImagePreviewNode(Node):
    def __init__(self):
        super().__init__('image_preview')
        self.declare_parameter('width', 320)
        self.declare_parameter('height', 320)
        self.declare_parameter('jpeg_quality', 60)
        self.declare_parameter('max_fps', 24.0)
        self.declare_parameter('streams', ['rgb', 'stereo'])

        max_fps = self.get_parameter('max_fps').value
        self.period = 1.0 / max_fps if max_fps > 0 else 0.0
        self.streams = [Stream(self, name) for name in self.get_parameter('streams').value]
        self.get_logger().info(
            f"Preview active: {self.get_parameter('width').value}x"
            f"{self.get_parameter('height').value} @ {max_fps} fps, "
            f"quality {self.get_parameter('jpeg_quality').value}")


def main(args=None):
    rclpy.init(args=args)
    node = ImagePreviewNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
