"""
ROS 2 Driver Node for Xsens MTi series (MTi-680G / MTi-7 / MTi-600).
Supports:
  - Direct Serial mode (/dev/ttyUSB0 on Linux/Jetson, or COM7 on Windows)
  - UDP network bridge mode (for Docker simulation without USB passthrough)
  - Auto mode (tries serial, falls back to UDP)

Publishes:
  - /gnss (sensor_msgs/msg/NavSatFix)
  - /imu/data (sensor_msgs/msg/Imu)
  - /filter/quaternion (geometry_msgs/msg/QuaternionStamped)
  - /filter/velocity (geometry_msgs/msg/TwistStamped)
"""

import json
import socket
import threading
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus
from geometry_msgs.msg import QuaternionStamped, TwistStamped

from xsens_mti_driver.xbus_parser import XbusParser

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class XsensNode(Node):
    def __init__(self):
        super().__init__('xsens_mti_node')

        # Declare ROS 2 parameters
        self.declare_parameter('device_mode', 'auto')        # 'auto', 'serial', 'udp'
        self.declare_parameter('serial_port', '/dev/ttyUSB0') # Default for Linux/Jetson
        self.declare_parameter('baudrate', 921600)
        self.declare_parameter('udp_host', '0.0.0.0')
        self.declare_parameter('udp_port', 9876)
        self.declare_parameter('imu_frame_id', 'imu_link')
        self.declare_parameter('gnss_frame_id', 'gnss_link')

        self.device_mode = self.get_parameter('device_mode').value
        self.serial_port = self.get_parameter('serial_port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.udp_host = self.get_parameter('udp_host').value
        self.udp_port = self.get_parameter('udp_port').value
        self.imu_frame_id = self.get_parameter('imu_frame_id').value
        self.gnss_frame_id = self.get_parameter('gnss_frame_id').value

        # Publishers
        self.pub_gnss = self.create_publisher(NavSatFix, '/gnss', 10)
        self.pub_imu = self.create_publisher(Imu, '/imu/data', 10)
        self.pub_quat = self.create_publisher(QuaternionStamped, '/filter/quaternion', 10)
        self.pub_vel = self.create_publisher(TwistStamped, '/filter/velocity', 10)

        self.running = True
        self.parser = XbusParser()

        self.get_logger().info(
            f"Initializing Xsens MTi Node. Requested mode: '{self.device_mode}'. "
            f"Serial: {self.serial_port} @ {self.baudrate}, UDP: {self.udp_host}:{self.udp_port}"
        )

        # Worker thread
        self.worker_thread = threading.Thread(target=self._run_driver, daemon=True)
        self.worker_thread.start()

    def _run_driver(self):
        mode = self.device_mode

        if mode == 'auto':
            # Try serial first
            if HAS_SERIAL:
                try:
                    self.get_logger().info(f"Attempting serial connection on '{self.serial_port}'...")
                    ser = serial.Serial(self.serial_port, self.baudrate, timeout=1.0)
                    self.get_logger().info(f"Successfully opened serial port '{self.serial_port}'!")
                    self._loop_serial(ser)
                    return
                except Exception as e:
                    self.get_logger().warn(
                        f"Serial port '{self.serial_port}' unavailable ({e}). "
                        f"Falling back to UDP Bridge mode on {self.udp_host}:{self.udp_port}..."
                    )
            else:
                self.get_logger().warn("pyserial not installed. Falling back to UDP Bridge mode...")

            self._loop_udp()

        elif mode == 'serial':
            if not HAS_SERIAL:
                self.get_logger().error("device_mode='serial' requested but pyserial is not installed!")
                return
            while self.running and rclpy.ok():
                try:
                    self.get_logger().info(f"Connecting to serial port '{self.serial_port}'...")
                    ser = serial.Serial(self.serial_port, self.baudrate, timeout=1.0)
                    self.get_logger().info(f"Serial connected to '{self.serial_port}'!")
                    self._loop_serial(ser)
                except Exception as e:
                    self.get_logger().warn(f"Serial error: {e}. Retrying in 2 seconds...")
                    time.sleep(2.0)

        elif mode == 'udp':
            self._loop_udp()

    def _loop_serial(self, ser: 'serial.Serial'):
        try:
            ser.reset_input_buffer()
            # Wake up device into Measurement Mode (FA FF 10 00 F1)
            ser.write(bytes([0xFA, 0xFF, 0x10, 0x00, 0xF1]))

            while self.running and rclpy.ok():
                chunk = ser.read(256)
                if not chunk:
                    continue
                self.parser.add_data(chunk)

                while True:
                    msg = self.parser.parse_next_message()
                    if msg is None:
                        break
                    mid, payload = msg
                    if mid == 0x36: # MTData2
                        data = self.parser.decode_mtdata2(payload)
                        self._publish_data(data)
        except Exception as e:
            self.get_logger().error(f"Serial exception: {e}")
        finally:
            try:
                ser.close()
            except Exception:
                pass

    def _loop_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.udp_host, self.udp_port))
        sock.settimeout(1.0)
        self.get_logger().info(f"UDP Bridge listening for telemetry on {self.udp_host}:{self.udp_port}...")

        while self.running and rclpy.ok():
            try:
                packet, _ = sock.recvfrom(4096)
                if not packet:
                    continue

                # Can receive either raw Xbus bytes or JSON formatted packet from bridge
                if packet.startswith(b'\xfa\xff'):
                    self.parser.add_data(packet)
                    while True:
                        msg = self.parser.parse_next_message()
                        if msg is None:
                            break
                        mid, payload = msg
                        if mid == 0x36:
                            data = self.parser.decode_mtdata2(payload)
                            self._publish_data(data)
                else:
                    # JSON payload
                    try:
                        data = json.loads(packet.decode('utf-8'))
                        self._publish_data(data)
                    except Exception:
                        pass
            except socket.timeout:
                continue
            except Exception as e:
                self.get_logger().warn(f"UDP error: {e}")
                time.sleep(1.0)

        sock.close()

    def _publish_data(self, data: dict):
        now = self.get_clock().now().to_msg()

        # 1. IMU Data (/imu/data)
        has_imu = ('quaternion' in data or 'acceleration' in data or 'rate_of_turn' in data)
        if has_imu:
            imu_msg = Imu()
            imu_msg.header.stamp = now
            imu_msg.header.frame_id = self.imu_frame_id

            if 'quaternion' in data:
                # MTi quaternion format: [q0, q1, q2, q3] -> [w, x, y, z]
                q = data['quaternion']
                imu_msg.orientation.w = float(q[0])
                imu_msg.orientation.x = float(q[1])
                imu_msg.orientation.y = float(q[2])
                imu_msg.orientation.z = float(q[3])
                imu_msg.orientation_covariance[0] = 0.001
                imu_msg.orientation_covariance[4] = 0.001
                imu_msg.orientation_covariance[8] = 0.001
            else:
                imu_msg.orientation_covariance[0] = -1.0 # Invalid orientation

            if 'rate_of_turn' in data:
                rot = data['rate_of_turn']
                imu_msg.angular_velocity.x = float(rot[0])
                imu_msg.angular_velocity.y = float(rot[1])
                imu_msg.angular_velocity.z = float(rot[2])
                imu_msg.angular_velocity_covariance[0] = 0.0001
                imu_msg.angular_velocity_covariance[4] = 0.0001
                imu_msg.angular_velocity_covariance[8] = 0.0001
            else:
                imu_msg.angular_velocity_covariance[0] = -1.0

            if 'acceleration' in data:
                acc = data['acceleration']
                imu_msg.linear_acceleration.x = float(acc[0])
                imu_msg.linear_acceleration.y = float(acc[1])
                imu_msg.linear_acceleration.z = float(acc[2])
                imu_msg.linear_acceleration_covariance[0] = 0.01
                imu_msg.linear_acceleration_covariance[4] = 0.01
                imu_msg.linear_acceleration_covariance[8] = 0.01
            else:
                imu_msg.linear_acceleration_covariance[0] = -1.0

            self.pub_imu.publish(imu_msg)

        # 2. Quaternion (/filter/quaternion)
        if 'quaternion' in data:
            q = data['quaternion']
            qs_msg = QuaternionStamped()
            qs_msg.header.stamp = now
            qs_msg.header.frame_id = self.imu_frame_id
            qs_msg.quaternion.w = float(q[0])
            qs_msg.quaternion.x = float(q[1])
            qs_msg.quaternion.y = float(q[2])
            qs_msg.quaternion.z = float(q[3])
            self.pub_quat.publish(qs_msg)

        # 3. GNSS / GPS (/gnss)
        gnss_msg = NavSatFix()
        gnss_msg.header.stamp = now
        gnss_msg.header.frame_id = self.gnss_frame_id

        if 'latitude' in data and 'longitude' in data and data.get('gnss_fix', False):
            gnss_msg.latitude = float(data['latitude'])
            gnss_msg.longitude = float(data['longitude'])
            gnss_msg.altitude = float(data.get('altitude', 0.0))

            rtk_status = data.get('rtk_status', 0)
            if rtk_status > 0:
                gnss_msg.status.status = NavSatStatus.STATUS_GBAS_FIX
            else:
                gnss_msg.status.status = NavSatStatus.STATUS_FIX

            gnss_msg.status.service = NavSatStatus.SERVICE_GPS
            gnss_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
            cov = 0.05 if rtk_status == 2 else 0.5
            gnss_msg.position_covariance[0] = cov
            gnss_msg.position_covariance[4] = cov
            gnss_msg.position_covariance[8] = cov * 4.0
            self.pub_gnss.publish(gnss_msg)
        else:
            # Indoors / Acquiring satellites: Publish NO_FIX status
            gnss_msg.status.status = NavSatStatus.STATUS_NO_FIX
            gnss_msg.status.service = NavSatStatus.SERVICE_GPS
            gnss_msg.latitude = float(data.get('latitude', 0.0))
            gnss_msg.longitude = float(data.get('longitude', 0.0))
            gnss_msg.altitude = float(data.get('altitude', 0.0))
            gnss_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
            self.pub_gnss.publish(gnss_msg)

        # 4. Velocity (/filter/velocity)
        if 'velocity' in data:
            vel = data['velocity']
            vel_msg = TwistStamped()
            vel_msg.header.stamp = now
            vel_msg.header.frame_id = self.imu_frame_id
            vel_msg.twist.linear.x = float(vel[0])
            vel_msg.twist.linear.y = float(vel[1])
            vel_msg.twist.linear.z = float(vel[2])
            self.pub_vel.publish(vel_msg)

    def destroy_node(self):
        self.running = False
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = XsensNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
