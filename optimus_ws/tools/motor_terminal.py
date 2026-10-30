#!/usr/bin/env python3
"""
Hugr Optimus - Interactive Terminal Motor Controller
Allows typing exact PWM values or using simple key commands to control the 4 motors.
"""

import sys
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from nav_msgs.msg import Odometry
import math

class MotorTerminal(Node):
    def __init__(self):
        super().__init__('motor_terminal')
        self.pub = self.create_publisher(Int32MultiArray, '/motor_pwms', 10)
        self.sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)
        self.pos = [0.0, 0.0]
        self.heading = 0.0
        self.speed = [0.0, 0.0, 0.0]

    def odom_callback(self, msg: Odometry):
        self.pos[0] = msg.pose.pose.position.x
        self.pos[1] = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.heading = math.degrees(math.atan2(siny_cosp, cosy_cosp)) % 360.0
        self.speed[0] = msg.twist.twist.linear.x
        self.speed[1] = msg.twist.twist.linear.y
        self.speed[2] = math.degrees(msg.twist.twist.angular.z)

    def send(self, pwms):
        msg = Int32MultiArray()
        msg.data = [int(p) for p in pwms]
        self.pub.publish(msg)
        rclpy.spin_once(self, timeout_sec=0.05)
        print(f"\n[ENVIADO A /motor_pwms] M1(Port)={pwms[0]}us, M2(Stbd)={pwms[1]}us, M3(Bow)={pwms[2]}us, M4(Stern)={pwms[3]}us")
        print(f"[ESTADO BARCO] Pos: X={self.pos[0]:+.2f}m, Y={self.pos[1]:+.2f}m | Rumbo={self.heading:5.1f}deg | Vel: u={self.speed[0]:+.2f}m/s, v={self.speed[1]:+.2f}m/s, yaw={self.speed[2]:+.1f}deg/s\n")

def main():
    rclpy.init()
    node = MotorTerminal()
    print("==========================================================")
    print(" Hugr Optimus - Consola Interactiva de Motores (/motor_pwms)")
    print(" Rango PWM: 1100 (Reversa Max) a 1900 (Avance Max), 1500 (Neutro/Stop)")
    print("==========================================================")
    print("Comandos disponibles:")
    print("  f   -> Avance suave (1650, 1650, 1500, 1500)")
    print("  ff  -> Avance rapido (1850, 1850, 1500, 1500)")
    print("  b   -> Atras (1350, 1350, 1500, 1500)")
    print("  l   -> Traslacion lateral babor (1500, 1500, 1700, 1700)")
    print("  r   -> Traslacion lateral estribor (1500, 1500, 1300, 1300)")
    print("  ql  -> Giro pivot babor (1300, 1700, 1700, 1300)")
    print("  qr  -> Giro pivot estribor (1700, 1300, 1300, 1700)")
    print("  s   -> PARADA (1500, 1500, 1500, 1500)")
    print("  o escribe 4 valores separados por espacio: ej. '1700 1700 1500 1500'")
    print("  exit -> Salir")
    print("==========================================================")

    while rclpy.ok():
        try:
            cmd = input("hugr@motores> ").strip().lower()
            if not cmd:
                continue
            if cmd in ['exit', 'quit', 'q']:
                break
            elif cmd == 'f':
                node.send([1650, 1650, 1500, 1500])
            elif cmd == 'ff':
                node.send([1850, 1850, 1500, 1500])
            elif cmd == 'b':
                node.send([1350, 1350, 1500, 1500])
            elif cmd == 'l':
                node.send([1500, 1500, 1700, 1700])
            elif cmd == 'r':
                node.send([1500, 1500, 1300, 1300])
            elif cmd == 'ql':
                node.send([1300, 1700, 1700, 1300])
            elif cmd == 'qr':
                node.send([1700, 1300, 1300, 1700])
            elif cmd == 's':
                node.send([1500, 1500, 1500, 1500])
            else:
                parts = cmd.split()
                if len(parts) == 4:
                    vals = [int(p) for p in parts]
                    node.send(vals)
                else:
                    print("[ERROR] Formato no reconocido. Usa 'f', 'b', 'l', 'r', 'ql', 'qr', 's' o escribe 4 numeros: '1700 1700 1500 1500'")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR]: {e}")

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
