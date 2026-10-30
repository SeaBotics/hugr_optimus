@echo off
title Hugr Optimus - Start Autonomous Buoy Circuit
echo ==========================================================
echo  Starting Autonomous Competition Buoy Circuit
echo  - Threading Gate 1 (Red/Green Buoys)
echo  - Threading Gate 2 (Red/Green Buoys)
echo  - Orbiting Yellow Pivot Buoy (360-deg rounding)
echo  - Returning Home through Gates 2 and 1
echo ==========================================================
wsl bash -l -c "source /opt/ros/jazzy/setup.bash && cd '$(wslpath '%~dp0..')' && source install/setup.bash && ros2 run hugr_autonomy send_destination --circuit"
pause
