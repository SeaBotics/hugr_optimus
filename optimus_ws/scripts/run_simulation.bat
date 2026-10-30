@echo off
title Hugr Optimus - Marine Simulation (Fossen SITL + RViz2)
echo ==========================================================
echo  Launching SeaBotics Hugr Optimus Marine Simulation
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && bash ./scripts/run_simulation.sh"
pause
