#!/usr/bin/env python3
"""
Windows Native Xbox Controller Bridge for ROS 2.
Reads Xbox Controller directly on Windows via XInput (no USB passthrough needed)
and streams joystick state via UDP to the WSL2 ROS 2 bridge at 50 Hz.
"""
import ctypes
from ctypes import wintypes
import socket
import json
import time
import sys

# Define XINPUT structures
class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('wButtons', wintypes.WORD),
        ('bLeftTrigger', wintypes.BYTE),
        ('bRightTrigger', wintypes.BYTE),
        ('sThumbLX', wintypes.SHORT),
        ('sThumbLY', wintypes.SHORT),
        ('sThumbRX', wintypes.SHORT),
        ('sThumbRY', wintypes.SHORT),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ('dwPacketNumber', wintypes.DWORD),
        ('Gamepad', XINPUT_GAMEPAD),
    ]

# Try loading XInput DLL
xinput_dll = None
for dll_name in ('xinput1_4.dll', 'xinput1_3.dll', 'xinput9_1_0.dll'):
    try:
        xinput_dll = ctypes.windll.LoadLibrary(dll_name)
        break
    except OSError:
        continue

if not xinput_dll:
    print("ERROR: Could not load any XInput DLL on Windows.")
    sys.exit(1)

# Set argument and return types
xinput_dll.XInputGetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
xinput_dll.XInputGetState.restype = wintypes.DWORD

# Standard Xbox buttons bitmask
XINPUT_GAMEPAD_DPAD_UP        = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN      = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT      = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT     = 0x0008
XINPUT_GAMEPAD_START          = 0x0010
XINPUT_GAMEPAD_BACK           = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB     = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB    = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER  = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A              = 0x1000
XINPUT_GAMEPAD_B              = 0x2000
XINPUT_GAMEPAD_X              = 0x4000
XINPUT_GAMEPAD_Y              = 0x8000

UDP_IP = "127.0.0.1"
UDP_PORT = 9872
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("==========================================================")
print("  Hugr Optimus - Windows Native Gamepad Bridge")
print("  Reads Xbox Controller via XInput -> Streams UDP to ROS 2")
print(f"  Destination: {UDP_IP}:{UDP_PORT} (WSL2)")
print("==========================================================")

state = XINPUT_STATE()
rate_hz = 50.0
dt = 1.0 / rate_hz

controller_connected = False

last_print_time = 0.0

try:
    while True:
        connected_slot = None
        for slot in range(4):
            res = xinput_dll.XInputGetState(slot, ctypes.byref(state))
            if res == 0:
                connected_slot = slot
                break

        if connected_slot is not None:
            if not controller_connected:
                print(f"[INFO] Xbox Controller Connected in Slot {connected_slot}! Streaming inputs to ROS 2...")
                controller_connected = True

            gp = state.Gamepad
            
            # Normalize thumbsticks to [-1.0, 1.0]
            lx = gp.sThumbLX / 32767.0
            ly = gp.sThumbLY / 32767.0
            rx = gp.sThumbRX / 32767.0
            ry = gp.sThumbRY / 32767.0
            
            lt = (gp.bLeftTrigger / 255.0) * 2.0 - 1.0
            rt = (gp.bRightTrigger / 255.0) * 2.0 - 1.0
            
            def deadzone(val, thresh=0.10):
                return val if abs(val) > thresh else 0.0

            dpad_x = 0.0
            if gp.wButtons & XINPUT_GAMEPAD_DPAD_LEFT:
                dpad_x = 1.0
            elif gp.wButtons & XINPUT_GAMEPAD_DPAD_RIGHT:
                dpad_x = -1.0

            dpad_y = 0.0
            if gp.wButtons & XINPUT_GAMEPAD_DPAD_UP:
                dpad_y = 1.0
            elif gp.wButtons & XINPUT_GAMEPAD_DPAD_DOWN:
                dpad_y = -1.0

            axes = [
                round(deadzone(lx), 4),
                round(deadzone(ly), 4),
                round(lt, 4),
                round(deadzone(rx), 4),
                round(deadzone(ry), 4),
                round(rt, 4),
                dpad_x,
                dpad_y
            ]

            buttons = [
                1 if (gp.wButtons & XINPUT_GAMEPAD_A) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_B) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_X) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_Y) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_RIGHT_SHOULDER) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_BACK) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_START) else 0,
                0, # Guide button
                1 if (gp.wButtons & XINPUT_GAMEPAD_LEFT_THUMB) else 0,
                1 if (gp.wButtons & XINPUT_GAMEPAD_RIGHT_THUMB) else 0,
            ]

            payload = json.dumps({"axes": axes, "buttons": buttons}).encode('utf-8')
            sock.sendto(payload, (UDP_IP, UDP_PORT))

            # Live console feedback (throttled to 2 Hz when active)
            now_t = time.time()
            is_active = any(abs(a) > 0.05 for a in [axes[0], axes[1], axes[3]])
            if is_active and (now_t - last_print_time >= 0.5):
                last_print_time = now_t
                print(f"[GAMEPAD WIN] Stick L: (Sway={axes[0]:+.2f}, Surge={axes[1]:+.2f}) | Stick R: (Yaw={axes[3]:+.2f}) -> UDP Sent")

        else:
            if controller_connected:
                print("[WARN] Controller disconnected. Waiting for connection...")
                controller_connected = False
            time.sleep(0.5)

        time.sleep(dt)

except KeyboardInterrupt:
    print("\nBridge stopped.")
