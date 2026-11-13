@echo off
title SeaBotics Hugr Optimus - 3D Gazebo Simulation Launcher
echo ==================================================================
echo  Launching SeaBotics Hugr Optimus 3D Gazebo Simulation
echo  Compatible with Windows 11 + WSL2 (Ubuntu 24.04 + ROS 2 Jazzy)
echo ==================================================================

:: Convert current Windows directory path to WSL format and execute the bash launcher
wsl bash -l -c "cd '$(wslpath '%~dp0')' && bash ./run_gazebo.sh %*"

pause
