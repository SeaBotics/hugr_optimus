@echo off
title Hugr Optimus - Autonomous Navigation
echo ==========================================================
echo  Launching SeaBotics Hugr Optimus Autonomous Navigator
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && bash ./scripts/run_autonomy.sh"
pause
