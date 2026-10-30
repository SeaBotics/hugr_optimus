"""
Windows to Docker / WSL UDP Bridge for Xsens MTi-680G.
Reads COM7 at 921600 baud and streams decoded telemetry / raw packets
over UDP to port 9876 for ROS 2 nodes running inside Docker or WSL.
"""

import json
import socket
import os
import sys
import time

try:
    import serial
except ImportError:
    print("Error: pyserial is required. Run: python -m pip install pyserial")
    sys.exit(1)

# Ensure src path is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from xsens_mti_driver.xbus_parser import XbusParser

PORT = 'COM7'
BAUD = 921600
UDP_TARGETS = ['127.0.0.1', '172.25.207.211']
UDP_TARGET_PORT = 9876

def main():
    print("=" * 60)
    print("  SeaBotics Hugr Optimus - Xsens Windows -> ROS 2 Bridge")
    print("=" * 60)
    print(f"Targeting hardware on {PORT} @ {BAUD} baud...")
    print(f"Streaming live telemetry to UDP {UDP_TARGETS}:{UDP_TARGET_PORT} (Docker / WSL)...")
    print("Press Ctrl+C to stop.\n")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    parser = XbusParser()

    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1.0)
            ser.reset_input_buffer()
            # Wake up sensor into Measurement Mode
            ser.write(XbusParser.create_message(0x10))
            time.sleep(0.1)
            print(f"[CONNECTED] Serial open on {PORT}. Streaming packets...")

            pkt_count = 0
            last_print = time.time()

            while True:
                chunk = ser.read(512)
                if not chunk:
                    continue

                parser.add_data(chunk)

                while True:
                    msg = parser.parse_next_message()
                    if msg is None:
                        break
                    mid, payload = msg
                    if mid == 0x36: # MTData2
                        data = parser.decode_mtdata2(payload)
                        pkt_count += 1

                        # Send to Docker / WSL via UDP
                        json_bytes = json.dumps(data).encode('utf-8')
                        for target in UDP_TARGETS:
                            try:
                                sock.sendto(json_bytes, (target, UDP_TARGET_PORT))
                            except Exception:
                                pass

                        # Terminal heartbeat once every 0.5s
                        if time.time() - last_print > 0.5:
                            last_print = time.time()
                            quat = data.get('quaternion', [0, 0, 0, 0])
                            lat = data.get('latitude', 0.0)
                            lon = data.get('longitude', 0.0)
                            fix = data.get('gnss_fix', False)
                            rtk = data.get('rtk_status', 0)
                            rtk_str = ["No RTK", "RTK Float", "RTK Fix"][rtk] if rtk <= 2 else "Unknown"

                            print(
                                f"[{pkt_count:6d} pkts] "
                                f"Quat: [{quat[0]:.2f}, {quat[1]:.2f}, {quat[2]:.2f}, {quat[3]:.2f}] | "
                                f"Lat: {lat:.6f}, Lon: {lon:.6f} | "
                                f"GPS Fix: {fix} ({rtk_str})"
                            )

        except KeyboardInterrupt:
            print("\nStopping bridge...")
            break
        except Exception as e:
            print(f"[RECONNECTING] Serial error: {e}. Retrying in 1s...")
            time.sleep(1.0)

    sock.close()
    print("Bridge stopped.")

if __name__ == '__main__':
    main()
