@echo off
title Hugr Optimus - 3D Gazebo Sim Marine Simulation
echo ==========================================================
echo  Launching SeaBotics Hugr Optimus Gazebo Simulation
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && bash ./scripts/run_gazebo.sh"
pause
