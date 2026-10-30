@echo off
title Hugr Optimus - Keyboard Teleop
echo ==========================================================
echo  Launching SeaBotics Hugr Optimus Keyboard Teleop
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && bash ./scripts/run_teleop.sh"
pause
