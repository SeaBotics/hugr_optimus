@echo off
title Hugr Optimus - Joystick Remote Control
echo ==========================================================
echo  Launching SeaBotics Hugr Optimus Joystick Remote Control
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && bash ./scripts/run_joystick.sh"
pause
