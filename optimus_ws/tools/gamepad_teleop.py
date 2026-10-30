#!/usr/bin/env python3
"""
Hugr Optimus - Windows Native Gamepad Teleoperation Controller.
Reads Xbox Controller directly on Windows via XInput, calculates 4-thruster PWMs,
posts them directly to the ROS 2 topic /motor_pwms in WSL,
and displays live terminal telemetry of the sticks, topic publication, and boat motion.
"""

import ctypes
from ctypes import wintypes
import urllib.request
import urllib.error
import json
import time
import sys
import os

# Set terminal color support on Windows
os.system('')

# XInput Structs
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

# Load XInput DLL
xinput_dll = None
for dll_name in ('xinput1_4.dll', 'xinput1_3.dll', 'xinput9_1_0.dll'):
    try:
        xinput_dll = ctypes.windll.LoadLibrary(dll_name)
        break
    except OSError:
        pass

if not xinput_dll:
    print("[ERROR] No se pudo cargar la librería XInput en Windows.")
    sys.exit(1)

xinput_dll.XInputGetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
xinput_dll.XInputGetState.restype = wintypes.DWORD

# Button masks
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

BRIDGE_URL = "http://127.0.0.1:8085/api/gamepad"

def deadzone(val, thresh=0.10):
    return val if abs(val) > thresh else 0.0

def clamp_pwm(val):
    return int(max(1100, min(1900, val)))

def main():
    print("\033[96m================================================================================\033[0m")
    print("\033[96m       🚢 SeaBotics Hugr Optimus - Teleoperación con Mando (Windows -> ROS 2)     \033[0m")
    print("\033[96m================================================================================\033[0m")
    print(" Buscando mando Xbox / DirectInput en Windows...")

    state = XINPUT_STATE()
    active_slot = None
    
    # Wait for controller
    while active_slot is None:
        for slot in range(4):
            if xinput_dll.XInputGetState(slot, ctypes.byref(state)) == 0:
                active_slot = slot
                break
        if active_slot is None:
            time.sleep(0.5)

    print(f"\033[92m[CONECTADO] Mando detectado en Slot {active_slot} de Windows!\033[0m")
    print(f" Conectando con receptor de ROS 2 en WSL2 ({BRIDGE_URL})...\n")
    print("\033[93mControles del Mando:\033[0m")
    print("  • Stick Izquierdo (Vertical):   Avance (+) / Retroceso (-)")
    print("  • Stick Izquierdo (Horizontal): Desplazamiento Lateral Babor (+) / Estribor (-)")
    print("  • Stick Derecho (Horizontal):   Giro Pivot Babor (+) / Estribor (-)")
    print("  • Botón A:                      Turbo (100% de potencia)")
    print("  • Botón B o LB:                 Parada de Emergencia (1500 us)")
    print("\033[96m================================================================================\033[0m\n")

    rate_hz = 25.0
    dt = 1.0 / rate_hz
    last_print = 0.0
    was_neutral = True
    server_connected = False

    while True:
        try:
            res = xinput_dll.XInputGetState(active_slot, ctypes.byref(state))
            if res != 0:
                print("\033[91m[DESCONECTADO] Se perdió la conexión con el mando. Reconectando...\033[0m")
                active_slot = None
                while active_slot is None:
                    for slot in range(4):
                        if xinput_dll.XInputGetState(slot, ctypes.byref(state)) == 0:
                            active_slot = slot
                            print(f"\033[92m[RECONECTADO] Mando en Slot {active_slot}!\033[0m")
                            break
                    time.sleep(0.5)
                continue

            gp = state.Gamepad

            # Read normalized stick axes [-1.0, 1.0]
            # Left Stick: Y is Surge (+1 Forward, -1 Backward), X is Sway (+1 Port/Left, -1 Starboard/Right)
            raw_surge = deadzone(gp.sThumbLY / 32767.0)
            raw_sway = -deadzone(gp.sThumbLX / 32767.0)  # Left on stick is +sway (Port)
            
            # Right Stick: X is Yaw (+1 Turn Port / CCW, -1 Turn Starboard / CW)
            raw_yaw = -deadzone(gp.sThumbRX / 32767.0)   # Left on stick is +yaw (CCW)

            # Check buttons
            btn_emergency = (gp.wButtons & XINPUT_GAMEPAD_B) or (gp.wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER)
            btn_turbo = bool(gp.wButtons & XINPUT_GAMEPAD_A) or bool(gp.bRightTrigger > 128)

            # Max power scale (75% default for smooth maneuvering, 100% with Turbo)
            power_scale = 1.0 if btn_turbo else 0.75

            if btn_emergency:
                surge = 0.0
                sway = 0.0
                yaw = 0.0
            else:
                surge = raw_surge * power_scale
                sway = raw_sway * power_scale
                yaw = raw_yaw * power_scale

            # Calculate 4 Thruster PWMs:
            # M1 (Port): Surge - 0.5 * Yaw
            # M2 (Starboard): Surge + 0.5 * Yaw
            # M3 (Bow): Sway + 0.5 * Yaw
            # M4 (Stern): Sway - 0.5 * Yaw
            m1_cmd = surge - 0.5 * yaw
            m2_cmd = surge + 0.5 * yaw
            m3_cmd = sway + 0.5 * yaw
            m4_cmd = sway - 0.5 * yaw

            pwm_m1 = clamp_pwm(1500 + round(400.0 * m1_cmd))
            pwm_m2 = clamp_pwm(1500 + round(400.0 * m2_cmd))
            pwm_m3 = clamp_pwm(1500 + round(400.0 * m3_cmd))
            pwm_m4 = clamp_pwm(1500 + round(400.0 * m4_cmd))

            pwms = [pwm_m1, pwm_m2, pwm_m3, pwm_m4]
            is_active = any(p != 1500 for p in pwms)

            # Build payload
            axes_arr = [raw_sway, raw_surge, 0.0, raw_yaw, 0.0, 0.0]
            buttons_arr = [1 if (gp.wButtons & (1 << b)) else 0 for b in range(12)]
            payload = json.dumps({
                "pwms": pwms,
                "surge": round(surge, 3),
                "sway": round(sway, 3),
                "yaw": round(yaw, 3),
                "axes": axes_arr,
                "buttons": buttons_arr
            }).encode('utf-8')

            # Send HTTP request to ROS 2 bridge
            telemetry = None
            try:
                req = urllib.request.Request(BRIDGE_URL, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=0.15) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                    telemetry = resp_data.get("telemetry", {})
                    if not server_connected:
                        print("\033[92m[CONEXION ESTABLECIDA] Conectado exitosamente con ROS 2 en WSL2!\033[0m\n")
                        server_connected = True
            except Exception as e:
                if server_connected or last_print == 0.0:
                    print(f"\033[93m[AVISO] Esperando al receptor ROS 2 en WSL2 ({BRIDGE_URL})...\033[0m")
                    server_connected = False

            now = time.time()

            # LIVE HUD PRINTING
            if is_active:
                was_neutral = False
                if now - last_print >= 0.2:  # 5 Hz refresh during active driving
                    last_print = now
                    telem_str = ""
                    if telemetry:
                        vel_u = telemetry.get('speed', {}).get('u', 0.0)
                        vel_v = telemetry.get('speed', {}).get('v', 0.0)
                        heading = telemetry.get('heading_deg', 0.0)
                        pos_x = telemetry.get('pos', {}).get('x', 0.0)
                        pos_y = telemetry.get('pos', {}).get('y', 0.0)
                        telem_str = f" | \033[93mBARCO: Vel={vel_u:+.2f}m/s, Rumbo={heading:5.1f}°, Pos=({pos_x:+.1f}m, {pos_y:+.1f}m)\033[0m"

                    turbo_label = " \033[91m[TURBO]\033[0m" if btn_turbo else ""
                    print(
                        f"\r\033[96m[MANDO]\033[0m Surge={surge:+.2f}, Sway={sway:+.2f}, Yaw={yaw:+.2f}{turbo_label} "
                        f"==> \033[92m/motor_pwms:\033[0m [M1={pwm_m1}, M2={pwm_m2}, M3={pwm_m3}, M4={pwm_m4}]"
                        f"{telem_str}   ",
                        end="", flush=True
                    )
            else:
                if not was_neutral:
                    print(f"\r\033[90m[MANDO NEUTRO] -> Publicado /motor_pwms: [1500, 1500, 1500, 1500] (Parada / Barco desacelerando)\033[0m                    ")
                    was_neutral = True

            time.sleep(dt)

        except KeyboardInterrupt:
            print("\n\nDeteniendo control de mando. Enviando parada neutra...")
            try:
                stop_payload = json.dumps({"pwms": [1500, 1500, 1500, 1500]}).encode('utf-8')
                req = urllib.request.Request(BRIDGE_URL, data=stop_payload, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=0.2)
            except Exception:
                pass
            print("Cerrado.")
            break

if __name__ == '__main__':
    main()
