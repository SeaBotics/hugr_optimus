"""
Xbus Binary Protocol Parser for Xsens MTi series (MTi-680G, MTi-7, MTi-600, MTi-1/10/100).
Decodes MTData2 (MID 0x36) packets into structured dictionary of measurements.
"""

import struct
from typing import Dict, Any, Optional, Tuple

class XbusParser:
    def __init__(self):
        self.buffer = bytearray()

    @staticmethod
    def calc_checksum(msg_bytes: bytes) -> int:
        """Returns checksum byte such that sum(msg_bytes[1:]) % 256 == 0."""
        s = sum(msg_bytes[1:]) % 256
        return (256 - s) % 256

    @classmethod
    def create_message(cls, mid: int, payload: bytes = b'') -> bytes:
        length = len(payload)
        if length < 255:
            header = bytes([0xFA, 0xFF, mid, length])
        else:
            header = bytes([0xFA, 0xFF, mid, 0xFF, (length >> 8) & 0xFF, length & 0xFF])
        msg = header + payload
        cs = cls.calc_checksum(msg)
        return msg + bytes([cs])

    def add_data(self, chunk: bytes):
        """Append incoming bytes to buffer."""
        self.buffer.extend(chunk)

    def parse_next_message(self) -> Optional[Tuple[int, bytes]]:
        """
        Extracts next valid (MID, payload) from the internal buffer.
        Returns None if no complete valid message is yet available.
        """
        while len(self.buffer) >= 5:
            idx = self.buffer.find(b'\xfa\xff')
            if idx == -1:
                self.buffer.clear()
                return None
            if idx > 0:
                del self.buffer[:idx]

            if len(self.buffer) < 4:
                return None

            mid = self.buffer[2]
            length = self.buffer[3]
            header_len = 4

            if length == 0xFF:
                if len(self.buffer) < 6:
                    return None
                length = (self.buffer[4] << 8) | self.buffer[5]
                header_len = 6

            total_msg_len = header_len + length + 1  # includes checksum
            if len(self.buffer) < total_msg_len:
                return None  # Wait for remaining bytes

            msg = bytes(self.buffer[:total_msg_len])
            del self.buffer[:total_msg_len]

            # Verify checksum
            if sum(msg[1:]) % 256 != 0:
                continue  # Corrupted packet, keep scanning

            payload = msg[header_len:-1]
            return mid, payload

        return None

    @staticmethod
    def decode_mtdata2(payload: bytes) -> Dict[str, Any]:
        """
        Decodes MTData2 payload (data fields) into dictionary.
        Supported fields:
          - packet_counter: uint16
          - sample_time_fine: uint32
          - quaternion: [q0, q1, q2, q3] (w, x, y, z)
          - euler: [roll, pitch, yaw] (degrees)
          - acceleration: [ax, ay, az] (m/s^2)
          - rate_of_turn: [gx, gy, gz] (rad/s)
          - latitude: degrees
          - longitude: degrees
          - altitude: meters
          - velocity: [vx, vy, vz] (m/s)
          - status_word: uint32
        """
        data: Dict[str, Any] = {}
        idx = 0
        total_len = len(payload)

        while idx + 3 <= total_len:
            data_id = (payload[idx] << 8) | payload[idx + 1]
            data_len = payload[idx + 2]
            idx += 3

            if idx + data_len > total_len:
                break

            field = payload[idx:idx + data_len]
            idx += data_len

            # Packet Counter
            if data_id == 0x1020 and data_len == 2:
                data['packet_counter'] = struct.unpack('>H', field)[0]

            # Sample Time Fine
            elif data_id == 0x1060 and data_len == 4:
                data['sample_time_fine'] = struct.unpack('>I', field)[0]

            # Orientation - Quaternion (single precision)
            elif (data_id & 0xFFF0) == 0x2010 and data_len == 16:
                q0, q1, q2, q3 = struct.unpack('>ffff', field)
                data['quaternion'] = [q0, q1, q2, q3]  # w, x, y, z

            # Orientation - Quaternion (double precision)
            elif (data_id & 0xFFF0) == 0x2010 and data_len == 32:
                q0, q1, q2, q3 = struct.unpack('>dddd', field)
                data['quaternion'] = [q0, q1, q2, q3]

            # Orientation - Euler angles (roll, pitch, yaw in deg)
            elif (data_id & 0xFFF0) == 0x2020 and data_len == 12:
                roll, pitch, yaw = struct.unpack('>fff', field)
                data['euler'] = [roll, pitch, yaw]

            # Acceleration (m/s^2)
            elif (data_id & 0xFFF0) == 0x4020 and data_len == 12:
                ax, ay, az = struct.unpack('>fff', field)
                data['acceleration'] = [ax, ay, az]

            # Rate of Turn / Gyro (rad/s)
            elif (data_id & 0xFFF0) == 0x8020 and data_len == 12:
                gx, gy, gz = struct.unpack('>fff', field)
                data['rate_of_turn'] = [gx, gy, gz]

            # Position Lat/Lon (float32 or float64)
            elif (data_id & 0xFFF0) == 0x5040:
                if data_len == 16:  # 2 doubles
                    lat, lon = struct.unpack('>dd', field)
                    data['latitude'] = lat
                    data['longitude'] = lon
                elif data_len == 8:  # 2 floats
                    lat, lon = struct.unpack('>ff', field)
                    data['latitude'] = lat
                    data['longitude'] = lon

            # Altitude (meters)
            elif (data_id & 0xFFF0) == 0x5020:
                if data_len == 8:
                    alt = struct.unpack('>d', field)[0]
                    data['altitude'] = alt
                elif data_len == 4:
                    alt = struct.unpack('>f', field)[0]
                    data['altitude'] = alt

            # Velocity XYZ (m/s)
            elif (data_id & 0xFFF0) == 0xD010 and data_len == 12:
                vx, vy, vz = struct.unpack('>fff', field)
                data['velocity'] = [vx, vy, vz]

            # Status Word
            elif data_id == 0x7010 and data_len == 4:
                status = struct.unpack('>I', field)[0]
                data['status_word'] = status
                # Bit 2: GNSS Fix flag
                data['gnss_fix'] = bool(status & (1 << 2))
                # Bit 24-25: RTK status (0: no RTK, 1: RTK Floating, 2: RTK Fixed)
                rtk_status = (status >> 24) & 0x03
                data['rtk_status'] = rtk_status

        return data
