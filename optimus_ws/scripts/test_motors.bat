@echo off
title Hugr Optimus - 4-Thruster Motor and Simulator Telemetry Verifier
echo ==========================================================
echo  Testing 4-Thruster Motor Commands & Odometry Telemetry
echo  (Forward Surge, Lateral Sway, Zero-Radius Pivot)
echo ==========================================================
wsl bash -l -c "source /opt/ros/jazzy/setup.bash && cd '$(wslpath '%~dp0..')' && source install/setup.bash && python3 tools/test_motors.py"
pause
