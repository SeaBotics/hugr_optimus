@echo off
title Hugr Optimus - Instant Hot-Reload Boat in Gazebo
echo ==========================================================
echo  Hot-reloading Hugr Optimus in Gazebo from model.sdf...
echo ==========================================================
wsl bash -l -c "source /opt/ros/jazzy/setup.bash && cd '$(wslpath '%~dp0..')' && source install/setup.bash && ./scripts/reload_boat.sh"
pause