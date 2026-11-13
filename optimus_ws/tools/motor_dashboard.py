#!/usr/bin/env python3
"""
Hugr Optimus - Interactive Marine Motor Control & Simulation Dashboard
Provides a real-time Web GUI on http://localhost:8080 to monitor, control,
and publish /motor_pwms commands to the ESP32 micro-ROS and Fossen simulator.
"""

import sys
import json
import math
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Float32MultiArray, Empty as RosEmpty, String as RosString
from nav_msgs.msg import Odometry
from std_srvs.srv import Empty

# Global vessel state shared between ROS and HTTP server
STATE = {
    "pwms": [1500, 1500, 1500, 1500],
    "thrusts": [0.0, 0.0, 0.0, 0.0],
    "pos": {"x": 0.0, "y": 0.0, "z": 0.0},
    "heading_deg": 0.0,
    "roll_deg": 0.0,
    "pitch_deg": 0.0,
    "speed": {"u": 0.0, "v": 0.0, "yaw_rate": 0.0},
    "wave": {"hs": 0.12, "length": 3.2, "dir": 40.0, "heave": 0.0},
    "autonomy": {
        "active": False,
        "status": "INACTIVO",
        "e_cross": 0.0,
        "heading_err_deg": 0.0,
        "dist_to_goal": 0.0,
        "wp_idx": 0,
        "total_wps": 0,
        "cmd_v": 0.0,
        "cmd_w": 0.0
    },
    "connected": False,
    "last_update": 0.0
}

class DashboardRosNode(Node):
    def __init__(self):
        super().__init__('motor_dashboard_node')
        self.pwm_pub = self.create_publisher(Int32MultiArray, '/motor_pwms', 10)
        self.circuit_pub = self.create_publisher(RosEmpty, '/autonomous/start_circuit', 10)
        self.cancel_pub = self.create_publisher(RosEmpty, '/cancel_destination', 10)
        self.pwm_sub = self.create_subscription(Int32MultiArray, '/motor_pwms', self.pwm_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)
        self.thrust_sub = self.create_subscription(Float32MultiArray, '/thrusters/actual_thrust', self.thrust_callback, 10)
        self.wave_sub = self.create_subscription(Float32MultiArray, '/environment/wave_telemetry', self.wave_callback, 10)
        self.autonomy_telem_sub = self.create_subscription(Float32MultiArray, '/autonomous/telemetry', self.autonomy_telem_callback, 10)
        self.autonomy_status_sub = self.create_subscription(RosString, '/autonomous/status', self.autonomy_status_callback, 10)
        self.reset_cli = self.create_client(Empty, '/hugr_sim/reset')
        self.get_logger().info("Motor Dashboard ROS 2 Node initialized. Publishing on /motor_pwms and /autonomous/start_circuit")

    def pwm_callback(self, msg: Int32MultiArray):
        if len(msg.data) >= 4:
            STATE["pwms"] = list(msg.data[:4])
            STATE["last_update"] = time.time()

    def thrust_callback(self, msg: Float32MultiArray):
        if len(msg.data) >= 4:
            STATE["thrusts"] = [round(float(v), 2) for v in msg.data[:4]]

    def wave_callback(self, msg: Float32MultiArray):
        if len(msg.data) >= 6:
            STATE["wave"]["hs"] = round(float(msg.data[0]), 2)
            STATE["wave"]["length"] = round(float(msg.data[1]), 1)
            STATE["wave"]["dir"] = round(float(msg.data[2]), 0)
            STATE["wave"]["heave"] = round(float(msg.data[3]), 2)

    def odom_callback(self, msg: Odometry):
        STATE["pos"]["x"] = round(float(msg.pose.pose.position.x), 2)
        STATE["pos"]["y"] = round(float(msg.pose.pose.position.y), 2)
        STATE["pos"]["z"] = round(float(msg.pose.pose.position.z), 2)
        
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        STATE["heading_deg"] = round(math.degrees(math.atan2(siny_cosp, cosy_cosp)) % 360.0, 1)

        sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        STATE["roll_deg"] = round(math.degrees(math.atan2(sinr_cosp, cosr_cosp)), 1)

        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        STATE["pitch_deg"] = round(math.degrees(math.asin(max(-1.0, min(1.0, sinp)))), 1)
        
        STATE["speed"]["u"] = round(float(msg.twist.twist.linear.x), 2)
        STATE["speed"]["v"] = round(float(msg.twist.twist.linear.y), 2)
        STATE["speed"]["yaw_rate"] = round(math.degrees(float(msg.twist.twist.angular.z)), 1)
        STATE["connected"] = True
        STATE["last_update"] = time.time()

    def publish_pwms(self, pwms):
        msg = Int32MultiArray()
        msg.data = [int(p) for p in pwms]
        self.pwm_pub.publish(msg)
        STATE["pwms"] = list(msg.data)
        STATE["last_update"] = time.time()

    def autonomy_telem_callback(self, msg: Float32MultiArray):
        if len(msg.data) >= 7:
            STATE["autonomy"]["e_cross"] = round(float(msg.data[0]), 2)
            STATE["autonomy"]["heading_err_deg"] = round(float(msg.data[1]), 1)
            STATE["autonomy"]["dist_to_goal"] = round(float(msg.data[2]), 2)
            STATE["autonomy"]["wp_idx"] = int(msg.data[3])
            STATE["autonomy"]["total_wps"] = int(msg.data[4])
            STATE["autonomy"]["cmd_v"] = round(float(msg.data[5]), 2)
            STATE["autonomy"]["cmd_w"] = round(float(msg.data[6]), 2)
            STATE["autonomy"]["active"] = True

    def autonomy_status_callback(self, msg: RosString):
        STATE["autonomy"]["status"] = msg.data

    def start_circuit(self):
        msg = RosEmpty()
        self.circuit_pub.publish(msg)
        STATE["autonomy"]["active"] = True
        STATE["autonomy"]["status"] = "INICIANDO CIRCUITO..."

    def stop_autonomy(self):
        msg = RosEmpty()
        self.cancel_pub.publish(msg)
        self.publish_pwms([1500, 1500, 1500, 1500])
        STATE["autonomy"]["active"] = False
        STATE["autonomy"]["status"] = "DETENIDO"

    def reset_vessel(self):
        if self.reset_cli.service_is_ready():
            req = Empty.Request()
            self.reset_cli.call_async(req)
        # Also send neutral stop
        self.publish_pwms([1500, 1500, 1500, 1500])

ROS_NODE = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hugr Optimus - Panel de Motores y Simulación ASV</title>
  <style>
    :root {
      --bg-dark: #0a0f1d;
      --bg-card: #131b2e;
      --bg-card-hover: #19243c;
      --primary: #00d2ff;
      --primary-hover: #3a7bd5;
      --accent: #00f2fe;
      --success: #00e676;
      --warning: #ffb300;
      --danger: #ff1744;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --border: #1e293b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-dark);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #080d1a;
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand h1 {
      font-size: 1.25rem;
      font-weight: 700;
      background: linear-gradient(90deg, #00d2ff, #00e676);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .brand-sub { font-size: 0.8rem; color: var(--text-muted); }
    .status-badges {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
      background: #1e293b;
    }
    .badge.active { background: rgba(0, 230, 118, 0.15); color: var(--success); border: 1px solid rgba(0, 230, 118, 0.4); }
    .badge.warn { background: rgba(255, 179, 0, 0.15); color: var(--warning); border: 1px solid rgba(255, 179, 0, 0.4); }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
    
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1.1fr 1fr;
      gap: 18px;
      padding: 20px;
      flex: 1;
    }
    @media (max-width: 1100px) {
      .main-grid { grid-template-columns: 1fr; }
    }
    
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .card-title {
      font-size: 1rem;
      font-weight: 700;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
    }
    .card-title span.tag {
      font-size: 0.7rem;
      color: var(--primary);
      background: rgba(0, 210, 255, 0.1);
      padding: 2px 8px;
      border-radius: 6px;
    }

    /* Motor sliders */
    .motor-control {
      background: #0f1627;
      border: 1px solid #1a253c;
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .motor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
      font-weight: 600;
    }
    .motor-badge {
      font-size: 0.75rem;
      padding: 2px 6px;
      border-radius: 4px;
      background: #1e293b;
      color: var(--primary);
    }
    .slider-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    input[type=range] {
      flex: 1;
      height: 8px;
      border-radius: 4px;
      background: #1e293b;
      outline: none;
      -webkit-appearance: none;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--primary);
      cursor: pointer;
      box-shadow: 0 0 10px var(--primary);
      border: 2px solid #fff;
    }
    .pwm-input {
      width: 72px;
      background: #172138;
      border: 1px solid var(--border);
      color: #fff;
      font-family: monospace;
      font-size: 0.95rem;
      font-weight: 700;
      padding: 5px 8px;
      border-radius: 6px;
      text-align: center;
    }
    .btn-reset-single {
      background: #1e293b;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      transition: all 0.2s;
    }
    .btn-reset-single:hover { background: #334155; color: #fff; }
    .motor-stats {
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .motor-stats strong { color: var(--text); }

    /* Sync checkbox */
    .sync-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      color: var(--text-muted);
      cursor: pointer;
      user-select: none;
    }

    /* Vessel Schematic Center */
    .vessel-schematic-wrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: #0c1221;
      border-radius: 12px;
      padding: 16px;
      border: 1px solid var(--border);
      position: relative;
      min-height: 380px;
    }
    svg.vessel-svg {
      width: 100%;
      max-width: 340px;
      height: auto;
      filter: drop-shadow(0 0 15px rgba(0, 210, 255, 0.15));
    }
    
    /* Preset Maneuvers Grid */
    .presets-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .btn-preset {
      background: #141f36;
      border: 1px solid #1f2f50;
      color: var(--text);
      padding: 10px 12px;
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-preset:hover {
      background: #1e2e4e;
      border-color: var(--primary);
      transform: translateY(-1px);
    }
    .btn-stop-all {
      grid-column: span 2;
      background: linear-gradient(135deg, #d32f2f, #f44336);
      border: 1px solid #ff5252;
      color: #fff;
      font-weight: 700;
      font-size: 0.9rem;
      padding: 12px;
      box-shadow: 0 0 15px rgba(244, 67, 54, 0.4);
    }
    .btn-stop-all:hover {
      background: linear-gradient(135deg, #f44336, #ff1744);
      transform: translateY(-2px);
    }

    /* Telemetry cards */
    .telemetry-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }
    .telem-box {
      background: #0f1627;
      border: 1px solid #1a253c;
      border-radius: 8px;
      padding: 10px;
      text-align: center;
    }
    .telem-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; }
    .telem-val { font-size: 1.25rem; font-weight: 700; color: var(--accent); margin-top: 2px; }

    /* Compass needle visual */
    .compass-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      padding: 10px;
      background: #0f1627;
      border-radius: 10px;
      border: 1px solid #1a253c;
    }
    .compass-dial {
      width: 70px;
      height: 70px;
      border-radius: 50%;
      border: 2px solid var(--border);
      position: relative;
      background: radial-gradient(circle, #131b2e 60%, #0a0f1d);
      box-shadow: inset 0 0 8px rgba(0,0,0,0.5);
    }
    .compass-needle {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 4px;
      height: 28px;
      background: linear-gradient(to top, #ff1744 50%, #00d2ff 50%);
      transform-origin: center center;
      transform: translate(-50%, -50%) rotate(0deg);
      border-radius: 2px;
      transition: transform 0.1s linear;
    }
    .compass-center {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 8px;
      height: 8px;
      background: #fff;
      border-radius: 50%;
      transform: translate(-50%, -50%);
    }

    /* Command preview box */
    .cmd-box {
      background: #070b14;
      border: 1px solid #1a253c;
      border-radius: 8px;
      padding: 10px;
      font-family: monospace;
      font-size: 0.75rem;
      color: #38bdf8;
      overflow-x: auto;
      user-select: all;
    }

    /* Footer info */
    footer {
      background: #080d1a;
      border-top: 1px solid var(--border);
      padding: 10px 24px;
      font-size: 0.75rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div style="font-size: 1.6rem;">🚢</div>
      <div>
        <h1>SeaBotics Hugr Optimus ASV</h1>
        <div class="brand-sub">Consola de Control de Motores y Dinámica Hidrodinámica Fossen</div>
      </div>
    </div>
    <div class="status-badges">
      <div class="badge active" id="badge-ros"><span class="dot"></span> ROS 2: /motor_pwms</div>
      <div class="badge" id="badge-status">50 Hz SITL</div>
      <button class="btn-preset" onclick="resetVessel()" style="padding: 4px 10px; font-size: 0.75rem;">🔄 Reset Posición</button>
    </div>
  </header>

  <div class="main-grid">
    <!-- COLUMNA 1: CONTROLES DE MOTORES -->
    <div class="card">
      <div class="card-title">
        <span>🎮 Comandos de Motores (PWM)</span>
        <span class="tag">ESP32 Nano / ESC</span>
      </div>

      <label class="sync-toggle">
        <input type="checkbox" id="sync-motors" checked>
        <span>Vincular M1 (Babor) y M2 (Estribor) para avance simétrico</span>
      </label>

      <!-- Motor 1: Port -->
      <div class="motor-control">
        <div class="motor-header">
          <span>M1: Babor (Port Lateral)</span>
          <span class="motor-badge" id="m1-badge">SURGE +X</span>
        </div>
        <div class="slider-row">
          <input type="range" id="m1-slider" min="1100" max="1900" value="1500" step="5" oninput="onSliderMove(0, this.value)">
          <input type="number" id="m1-input" class="pwm-input" min="1100" max="1900" value="1500" onchange="onInputVal(0, this.value)">
          <button class="btn-reset-single" onclick="resetSingleMotor(0)">1500</button>
        </div>
        <div class="motor-stats">
          <span>Potencia: <strong id="m1-pct">0%</strong></span>
          <span>Empuje: <strong id="m1-thrust">+0.0 N</strong></span>
        </div>
      </div>

      <!-- Motor 2: Starboard -->
      <div class="motor-control">
        <div class="motor-header">
          <span>M2: Estribor (Starboard Lateral)</span>
          <span class="motor-badge" id="m2-badge">SURGE +X</span>
        </div>
        <div class="slider-row">
          <input type="range" id="m2-slider" min="1100" max="1900" value="1500" step="5" oninput="onSliderMove(1, this.value)">
          <input type="number" id="m2-input" class="pwm-input" min="1100" max="1900" value="1500" onchange="onInputVal(1, this.value)">
          <button class="btn-reset-single" onclick="resetSingleMotor(1)">1500</button>
        </div>
        <div class="motor-stats">
          <span>Potencia: <strong id="m2-pct">0%</strong></span>
          <span>Empuje: <strong id="m2-thrust">+0.0 N</strong></span>
        </div>
      </div>

      <!-- Motor 3: Bow Transverse -->
      <div class="motor-control">
        <div class="motor-header">
          <span>M3: Túnel Proa (Bow Transverse)</span>
          <span class="motor-badge" id="m3-badge">SWAY / YAW</span>
        </div>
        <div class="slider-row">
          <input type="range" id="m3-slider" min="1100" max="1900" value="1500" step="5" oninput="onSliderMove(2, this.value)">
          <input type="number" id="m3-input" class="pwm-input" min="1100" max="1900" value="1500" onchange="onInputVal(2, this.value)">
          <button class="btn-reset-single" onclick="resetSingleMotor(2)">1500</button>
        </div>
        <div class="motor-stats">
          <span>Potencia: <strong id="m3-pct">0%</strong></span>
          <span>Empuje: <strong id="m3-thrust">+0.0 N</strong></span>
        </div>
      </div>

      <!-- Motor 4: Stern Transverse -->
      <div class="motor-control">
        <div class="motor-header">
          <span>M4: Túnel Popa (Stern Transverse)</span>
          <span class="motor-badge" id="m4-badge">SWAY / YAW</span>
        </div>
        <div class="slider-row">
          <input type="range" id="m4-slider" min="1100" max="1900" value="1500" step="5" oninput="onSliderMove(3, this.value)">
          <input type="number" id="m4-input" class="pwm-input" min="1100" max="1900" value="1500" onchange="onInputVal(3, this.value)">
          <button class="btn-reset-single" onclick="resetSingleMotor(3)">1500</button>
        </div>
        <div class="motor-stats">
          <span>Potencia: <strong id="m4-pct">0%</strong></span>
          <span>Empuje: <strong id="m4-thrust">+0.0 N</strong></span>
        </div>
      </div>

      <div style="font-size: 0.75rem; color: var(--text-muted); line-height: 1.4;">
        💡 <strong>Atajos de teclado:</strong> <code>W/S</code> Avance/Atrás, <code>A/D</code> Desplazamiento Lateral, <code>Q/E</code> Giro Pivot, <code>Espacio</code> Parada Inmediata.
      </div>
    </div>

    <!-- COLUMNA 2: VISUALIZACIÓN DINÁMICA DEL CATAMARÁN -->
    <div class="card">
      <div class="card-title">
        <span>🧭 Disposición de Propulsores (CAD STEP)</span>
        <span class="tag">Visualizador 2D</span>
      </div>

      <div class="vessel-schematic-wrap">
        <svg class="vessel-svg" viewBox="0 0 300 420" xmlns="http://www.w3.org/2000/svg">
          <!-- Calm Water Outline -->
          <rect width="300" height="420" fill="#08101e" rx="10"/>
          <path d="M 0 50 Q 75 40 150 50 T 300 50" fill="none" stroke="#0e1a30" stroke-width="2"/>
          <path d="M 0 150 Q 75 160 150 150 T 300 150" fill="none" stroke="#0e1a30" stroke-width="2"/>
          <path d="M 0 250 Q 75 240 150 250 T 300 250" fill="none" stroke="#0e1a30" stroke-width="2"/>
          <path d="M 0 350 Q 75 360 150 350 T 300 350" fill="none" stroke="#0e1a30" stroke-width="2"/>

          <!-- Catamaran Left Pontoon (Port Hull) -->
          <path d="M 70 80 Q 70 30 85 20 Q 100 30 100 80 L 100 350 Q 100 370 85 370 Q 70 370 70 350 Z" 
                fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>
          
          <!-- Catamaran Right Pontoon (Starboard Hull) -->
          <path d="M 200 80 Q 200 30 215 20 Q 230 30 230 80 L 230 350 Q 230 370 215 370 Q 200 370 200 350 Z" 
                fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>

          <!-- Cross Deck / Fuselage -->
          <rect x="95" y="110" width="110" height="190" rx="8" fill="#131e33" stroke="#475569" stroke-width="1.5"/>
          <rect x="110" y="140" width="80" height="120" rx="6" fill="#0d1424" stroke="#00d2ff" stroke-width="1.2" stroke-dasharray="3,3"/>
          <text x="150" y="200" fill="#64748b" font-size="10" text-anchor="middle" font-family="monospace">JETSON & BATTERY</text>

          <!-- PROA / BOW Marker -->
          <polygon points="150,15 156,28 144,28" fill="#00e676"/>
          <text x="150" y="42" fill="#00e676" font-size="11" font-weight="700" text-anchor="middle">PROA (BOW +X)</text>
          <text x="150" y="390" fill="#94a3b8" font-size="10" text-anchor="middle">POPA (STERN -X)</text>

          <!-- MOTOR 3: Bow Transverse Thruster (T_200_203) -->
          <g id="svg-m3-group">
            <rect x="132" y="70" width="36" height="16" rx="4" fill="#0284c7" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="150" y="82" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">M3</text>
            <!-- Thrust Vector Arrow (Lateral) -->
            <line id="vec-m3" x1="150" y1="78" x2="150" y2="78" stroke="#00e676" stroke-width="4" stroke-linecap="round"/>
          </g>

          <!-- MOTOR 4: Stern Transverse Thruster (T_201) -->
          <g id="svg-m4-group">
            <rect x="132" y="335" width="36" height="16" rx="4" fill="#0284c7" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="150" y="347" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">M4</text>
            <!-- Thrust Vector Arrow (Lateral) -->
            <line id="vec-m4" x1="150" y1="343" x2="150" y2="343" stroke="#00e676" stroke-width="4" stroke-linecap="round"/>
          </g>

          <!-- MOTOR 1: Port Lateral Thruster (T_200_202) -->
          <g id="svg-m1-group">
            <rect x="58" y="260" width="16" height="40" rx="4" fill="#0284c7" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="66" y="284" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">M1</text>
            <!-- Thrust Vector Arrow (Longitudinal) -->
            <line id="vec-m1" x1="66" y1="280" x2="66" y2="280" stroke="#00e676" stroke-width="4" stroke-linecap="round"/>
          </g>

          <!-- MOTOR 2: Starboard Lateral Thruster (T_200) -->
          <g id="svg-m2-group">
            <rect x="226" y="260" width="16" height="40" rx="4" fill="#0284c7" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="234" y="284" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">M2</text>
            <!-- Thrust Vector Arrow (Longitudinal) -->
            <line id="vec-m2" x1="234" y1="280" x2="234" y2="280" stroke="#00e676" stroke-width="4" stroke-linecap="round"/>
          </g>

          <!-- Center of Gravity (CG) Origin -->
          <circle cx="150" cy="220" r="5" fill="#f59e0b"/>
          <circle cx="150" cy="220" r="10" fill="none" stroke="#f59e0b" stroke-width="1" stroke-dasharray="2,2"/>
          <text x="150" y="240" fill="#f59e0b" font-size="9" text-anchor="middle">CG (0,0)</text>
        </svg>
      </div>

      <!-- Live Heading Compass -->
      <div class="compass-wrap">
        <div class="compass-dial">
          <div class="compass-needle" id="compass-needle"></div>
          <div class="compass-center"></div>
        </div>
        <div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">RUMBO ACTUAL (HEADING)</div>
          <div style="font-size: 1.4rem; font-weight: 700; color: #fff;" id="heading-display">0.0°</div>
          <div style="font-size: 0.75rem; color: var(--primary);" id="heading-cardinal">NORTE (000°)</div>
        </div>
      </div>
    </div>

    <!-- COLUMNA 3: MANIOBRAS Y TELEMETRÍA -->
    <div class="card">
      <div class="card-title">
        <span>⚡ Maniobras Rápidas</span>
        <span class="tag">Presets</span>
      </div>

      <div class="presets-grid">
        <button class="btn-preset" onclick="setPreset([1700, 1700, 1500, 1500])">🚢 Avance Crucero</button>
        <button class="btn-preset" onclick="setPreset([1900, 1900, 1500, 1500])">⚡ Avance Máximo</button>
        <button class="btn-preset" onclick="setPreset([1300, 1300, 1500, 1500])">🔙 Retroceso</button>
        <button class="btn-preset" onclick="setPreset([1500, 1500, 1700, 1700])">⬅️ Desplazar Babor</button>
        <button class="btn-preset" onclick="setPreset([1500, 1500, 1300, 1300])">➡️ Desplazar Estribor</button>
        <button class="btn-preset" onclick="setPreset([1300, 1700, 1700, 1300])">🔄 Pivot Babor (CCW)</button>
        <button class="btn-preset" onclick="setPreset([1700, 1300, 1300, 1700])">🔄 Pivot Estribor (CW)</button>
        <button class="btn-preset btn-stop-all" onclick="stopAll()">🛑 PARADA INMEDIATA (1500)</button>
      </div>

      <div class="card-title" style="margin-top: 10px;">
        <span>📊 Telemetría Hidrodinámica</span>
        <span class="tag">Odometría Fossen</span>
      </div>

      <div class="telemetry-grid">
        <div class="telem-box">
          <div class="telem-label">Posición X (Este)</div>
          <div class="telem-val" id="telem-x">+0.00 m</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Posición Y (Norte)</div>
          <div class="telem-val" id="telem-y">+0.00 m</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Velocidad Avance (u)</div>
          <div class="telem-val" id="telem-u">0.00 m/s</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Velocidad Lateral (v)</div>
          <div class="telem-val" id="telem-v">0.00 m/s</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Balanceo (Roll)</div>
          <div class="telem-val" id="telem-roll" style="color: #38bdf8;">+0.0°</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Cabeceo (Pitch)</div>
          <div class="telem-val" id="telem-pitch" style="color: #38bdf8;">+0.0°</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Oleaje (Heave Z)</div>
          <div class="telem-val" id="telem-heave" style="color: #00e676;">+0.0 cm</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Tasa de Giro (Yaw Rate)</div>
          <div class="telem-val" id="telem-yaw">0.0 °/s</div>
        </div>
      </div>

      <div class="card-title" style="margin-top: 14px;">
        <span>🏁 Autonomía & Circuito de Boyas</span>
        <span class="tag" id="auto-mode-badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981;">LOS GUIDANCE</span>
      </div>

      <div style="display: flex; gap: 8px; margin-bottom: 8px;">
        <button class="btn-preset" onclick="startCircuit()" style="background: linear-gradient(135deg, #059669, #10b981); color: #fff; font-weight: 700; flex: 2; padding: 8px;">
          🚀 Iniciar Circuito de Boyas
        </button>
        <button class="btn-preset btn-stop-all" onclick="stopAutonomy()" style="flex: 1; padding: 8px;">
          ⏹ Parar
        </button>
      </div>

      <div class="telemetry-grid">
        <div class="telem-box">
          <div class="telem-label">Estado Guiado</div>
          <div class="telem-val" id="auto-status" style="font-size: 0.82rem; color: #38bdf8;">INACTIVO</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Punto de Paso (WP)</div>
          <div class="telem-val" id="auto-wp" style="color: #a78bfa;">0 / 9</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Desviación Trayectoria (e)</div>
          <div class="telem-val" id="auto-cross-err" style="color: #00e676;">+0.00 m</div>
        </div>
        <div class="telem-box">
          <div class="telem-label">Error Rumbo (Yaw Err)</div>
          <div class="telem-val" id="auto-heading-err" style="color: #38bdf8;">0.0°</div>
        </div>
      </div>

      <div class="card-title" style="margin-top: 10px;">
        <span>💻 Comando ROS 2 Actual</span>
      </div>
      <div class="cmd-box" id="cmd-preview">
        ros2 topic pub /motor_pwms std_msgs/msg/Int32MultiArray "{data: [1500, 1500, 1500, 1500]}" --once
      </div>
    </div>
  </div>

  <footer>
    <div>Hugr Optimus SITL • SeaBotics Catamaran Marine Simulation • ROS 2 Jazzy</div>
    <div>Topic Activo: <code>/motor_pwms</code> [std_msgs/msg/Int32MultiArray]</div>
  </footer>

  <script>
    let currentPwms = [1500, 1500, 1500, 1500];
    let isUserInteracting = false;
    let pollInterval = null;

    function pwmsToPercent(pwm) {
      let pct = ((pwm - 1500) / 400.0) * 100.0;
      return (pct >= 0 ? "+" : "") + Math.round(pct) + "%";
    }

    function onSliderMove(idx, val) {
      isUserInteracting = true;
      val = parseInt(val);
      currentPwms[idx] = val;
      
      // If sync is enabled and moving M1 or M2, sync them:
      if (document.getElementById('sync-motors').checked && (idx === 0 || idx === 1)) {
        currentPwms[0] = val;
        currentPwms[1] = val;
        document.getElementById('m1-slider').value = val;
        document.getElementById('m1-input').value = val;
        document.getElementById('m2-slider').value = val;
        document.getElementById('m2-input').value = val;
      } else {
        document.getElementById(`m${idx+1}-input`).value = val;
      }
      sendPwmsToServer(currentPwms);
      updateVectorVisuals();
    }

    function onInputVal(idx, val) {
      val = Math.max(1100, Math.min(1900, parseInt(val) || 1500));
      currentPwms[idx] = val;
      document.getElementById(`m${idx+1}-slider`).value = val;
      document.getElementById(`m${idx+1}-input`).value = val;
      if (document.getElementById('sync-motors').checked && (idx === 0 || idx === 1)) {
        currentPwms[0] = val;
        currentPwms[1] = val;
        document.getElementById('m1-slider').value = val;
        document.getElementById('m1-input').value = val;
        document.getElementById('m2-slider').value = val;
        document.getElementById('m2-input').value = val;
      }
      sendPwmsToServer(currentPwms);
      updateVectorVisuals();
    }

    function resetSingleMotor(idx) {
      currentPwms[idx] = 1500;
      document.getElementById(`m${idx+1}-slider`).value = 1500;
      document.getElementById(`m${idx+1}-input`).value = 1500;
      if (document.getElementById('sync-motors').checked && (idx === 0 || idx === 1)) {
        currentPwms[0] = 1500;
        currentPwms[1] = 1500;
        document.getElementById('m1-slider').value = 1500;
        document.getElementById('m1-input').value = 1500;
        document.getElementById('m2-slider').value = 1500;
        document.getElementById('m2-input').value = 1500;
      }
      sendPwmsToServer(currentPwms);
      updateVectorVisuals();
    }

    function setPreset(pwms) {
      isUserInteracting = true;
      currentPwms = [...pwms];
      for (let i = 0; i < 4; i++) {
        document.getElementById(`m${i+1}-slider`).value = currentPwms[i];
        document.getElementById(`m${i+1}-input`).value = currentPwms[i];
      }
      sendPwmsToServer(currentPwms);
      updateVectorVisuals();
    }

    function stopAll() {
      setPreset([1500, 1500, 1500, 1500]);
    }

    function resetVessel() {
      stopAll();
      fetch('/api/reset', { method: 'POST' });
    }

    function sendPwmsToServer(pwms) {
      fetch('/api/set_pwms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pwms: pwms })
      }).catch(err => console.error("Error sending PWMs:", err));

      document.getElementById('cmd-preview').textContent = 
        `ros2 topic pub /motor_pwms std_msgs/msg/Int32MultiArray "{data: [${pwms.join(', ')}]}" --once`;
    }

    function updateVectorVisuals() {
      // M1 (Port, +X forward)
      let d1 = (currentPwms[0] - 1500) * 0.12; // arrow length
      let vec1 = document.getElementById('vec-m1');
      vec1.setAttribute('y2', (280 - d1));
      vec1.setAttribute('stroke', d1 >= 0 ? '#00e676' : '#ff1744');

      // M2 (Stbd, +X forward)
      let d2 = (currentPwms[1] - 1500) * 0.12;
      let vec2 = document.getElementById('vec-m2');
      vec2.setAttribute('y2', (280 - d2));
      vec2.setAttribute('stroke', d2 >= 0 ? '#00e676' : '#ff1744');

      // M3 (Bow, +Y port)
      let d3 = (currentPwms[2] - 1500) * 0.12;
      let vec3 = document.getElementById('vec-m3');
      vec3.setAttribute('x2', (150 - d3));
      vec3.setAttribute('stroke', d3 >= 0 ? '#00d2ff' : '#f59e0b');

      // M4 (Stern, +Y port)
      let d4 = (currentPwms[3] - 1500) * 0.12;
      let vec4 = document.getElementById('vec-m4');
      vec4.setAttribute('x2', (150 - d4));
      vec4.setAttribute('stroke', d4 >= 0 ? '#00d2ff' : '#f59e0b');

      for (let i = 0; i < 4; i++) {
        document.getElementById(`m${i+1}-pct`).textContent = pwmsToPercent(currentPwms[i]);
      }
    }

    async function pollState() {
      try {
        let res = await fetch('/api/state');
        let data = await res.json();
        
        // Update live odometry telemetry
        document.getElementById('telem-x').textContent = (data.pos.x >= 0 ? "+" : "") + data.pos.x.toFixed(2) + " m";
        document.getElementById('telem-y').textContent = (data.pos.y >= 0 ? "+" : "") + data.pos.y.toFixed(2) + " m";
        document.getElementById('telem-u').textContent = data.speed.u.toFixed(2) + " m/s (" + (data.speed.u * 1.94384).toFixed(1) + " kn)";
        document.getElementById('telem-v').textContent = data.speed.v.toFixed(2) + " m/s";
        document.getElementById('telem-yaw').textContent = data.speed.yaw_rate.toFixed(1) + " °/s";

        // Wave induced attitude (Roll, Pitch, Heave)
        if (data.roll_deg !== undefined) {
          document.getElementById('telem-roll').textContent = (data.roll_deg >= 0 ? "+" : "") + data.roll_deg.toFixed(1) + "°";
        }
        if (data.pitch_deg !== undefined) {
          document.getElementById('telem-pitch').textContent = (data.pitch_deg >= 0 ? "+" : "") + data.pitch_deg.toFixed(1) + "°";
        }
        if (data.pos && data.pos.z !== undefined) {
          document.getElementById('telem-heave').textContent = (data.pos.z >= 0 ? "+" : "") + (data.pos.z * 100).toFixed(0) + " cm";
        }

        // Heading compass
        let deg = data.heading_deg;
        document.getElementById('heading-display').textContent = deg.toFixed(1) + "°";
        document.getElementById('compass-needle').style.transform = `translate(-50%, -50%) rotate(${deg}deg)`;

        // Cardinal text
        let cardinal = "NORTE";
        if (deg >= 22.5 && deg < 67.5) cardinal = "NORESTE (NE)";
        else if (deg >= 67.5 && deg < 112.5) cardinal = "ESTE (E)";
        else if (deg >= 112.5 && deg < 157.5) cardinal = "SURESTE (SE)";
        else if (deg >= 157.5 && deg < 202.5) cardinal = "SUR (S)";
        else if (deg >= 202.5 && deg < 247.5) cardinal = "SUROESTE (SW)";
        else if (deg >= 247.5 && deg < 292.5) cardinal = "OESTE (W)";
        else if (deg >= 292.5 && deg < 337.5) cardinal = "NOROESTE (NW)";
        document.getElementById('heading-cardinal').textContent = `${cardinal} (${Math.round(deg).toString().padStart(3, '0')}°)`;

        // Update thrust numbers if provided
        if (data.thrusts) {
          for (let i = 0; i < 4; i++) {
            let t = data.thrusts[i] || 0.0;
            document.getElementById(`m${i+1}-thrust`).textContent = (t >= 0 ? "+" : "") + t.toFixed(1) + " N";
          }
        }

        // If another source (like gamepad or CLI) updated PWMs and user is not currently dragging:
        if (!isUserInteracting && data.pwms) {
          currentPwms = [...data.pwms];
          for (let i = 0; i < 4; i++) {
            document.getElementById(`m${i+1}-slider`).value = currentPwms[i];
            document.getElementById(`m${i+1}-input`).value = currentPwms[i];
          }
          updateVectorVisuals();
        }

        // Update Autonomy Telemetry
        if (data.autonomy) {
          let a = data.autonomy;
          let stEl = document.getElementById('auto-status');
          if (stEl) {
            stEl.textContent = a.status || "INACTIVO";
            stEl.style.color = a.active ? "#00e676" : "#94a3b8";
          }
          let wpEl = document.getElementById('auto-wp');
          if (wpEl) {
            wpEl.textContent = `${a.wp_idx} / ${a.total_wps}`;
          }

          let crEl = document.getElementById('auto-cross-err');
          if (crEl) {
            let err = a.e_cross || 0.0;
            crEl.textContent = (err >= 0 ? "+" : "") + err.toFixed(2) + " m";
            if (Math.abs(err) < 0.25) crEl.style.color = "#00e676";
            else if (Math.abs(err) < 0.6) crEl.style.color = "#f59e0b";
            else crEl.style.color = "#ff1744";
          }

          let hEl = document.getElementById('auto-heading-err');
          if (hEl) {
            let herr = a.heading_err_deg || 0.0;
            hEl.textContent = (herr >= 0 ? "+" : "") + herr.toFixed(1) + "°";
          }
        }

        let badge = document.getElementById('badge-ros');
        if (data.connected) {
          badge.className = "badge active";
          badge.innerHTML = '<span class="dot"></span> Sim Conectado: /motor_pwms';
        } else {
          badge.className = "badge warn";
          badge.innerHTML = '<span class="dot"></span> Esperando /odometry...';
        }
      } catch (e) {
        let badge = document.getElementById('badge-ros');
        badge.className = "badge warn";
        badge.innerHTML = '<span class="dot"></span> Desconectado';
      }
    }

    async function startCircuit() {
      try {
        await fetch('/api/start_circuit', { method: 'POST' });
      } catch (e) {
        console.error("Error starting buoy circuit:", e);
      }
    }

    async function stopAutonomy() {
      try {
        await fetch('/api/stop_autonomy', { method: 'POST' });
      } catch (e) {
        console.error("Error stopping autonomy:", e);
      }
    }

    // Keyboard controls
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') return;
      let handled = true;
      switch(e.key.toUpperCase()) {
        case 'W': setPreset([1750, 1750, 1500, 1500]); break; // Forward
        case 'S': setPreset([1250, 1250, 1500, 1500]); break; // Reverse
        case 'A': setPreset([1500, 1500, 1750, 1750]); break; // Strafe Port
        case 'D': setPreset([1500, 1500, 1250, 1250]); break; // Strafe Starboard
        case 'Q': setPreset([1300, 1700, 1700, 1300]); break; // Pivot Left
        case 'E': setPreset([1700, 1300, 1300, 1700]); break; // Pivot Right
        case ' ': stopAll(); break;                          // Space = Stop
        default: handled = false;
      }
      if (handled) e.preventDefault();
    });

    window.addEventListener('mouseup', () => { isUserInteracting = false; });
    window.addEventListener('touchend', () => { isUserInteracting = false; });

    updateVectorVisuals();
    pollInterval = setInterval(pollState, 100);
  </script>
</body>
</html>
"""

class DashboardHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress routine GET logging for a clean terminal
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/' or parsed.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif parsed.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(STATE).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8')

        if parsed.path == '/api/set_pwms':
            try:
                data = json.loads(body)
                pwms = data.get('pwms', [1500, 1500, 1500, 1500])
                if ROS_NODE is not None:
                    ROS_NODE.publish_pwms(pwms)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        elif parsed.path == '/api/reset':
            if ROS_NODE is not None:
                ROS_NODE.reset_vessel()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif parsed.path == '/api/start_circuit':
            if ROS_NODE is not None:
                ROS_NODE.start_circuit()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif parsed.path == '/api/stop_autonomy':
            if ROS_NODE is not None:
                ROS_NODE.stop_autonomy()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

def run_http_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), DashboardHttpHandler)
    print(f"\n[DASHBOARD READY] Open your browser at: http://localhost:{port}")
    server.serve_forever()

def main():
    global ROS_NODE
    rclpy.init()
    ROS_NODE = DashboardRosNode()

    # Start HTTP server in a daemon thread
    http_thread = threading.Thread(target=run_http_server, args=(8080,), daemon=True)
    http_thread.start()

    print("==========================================================")
    print(" Hugr Optimus - ASV Marine Motor & Simulation Dashboard")
    print(" Listening and publishing on topic: /motor_pwms")
    print(" Server running on http://localhost:8080")
    print(" Press Ctrl+C to exit")
    print("==========================================================")

    try:
        rclpy.spin(ROS_NODE)
    except KeyboardInterrupt:
        pass
    finally:
        ROS_NODE.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
