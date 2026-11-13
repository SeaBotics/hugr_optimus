@echo off
title Hugr Optimus - Motor Dashboard
echo ==========================================================
echo  Launching SeaBotics Hugr Optimus Motor Dashboard
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && bash ./scripts/run_motor_dashboard.sh"
pause
