@echo off
title Hugr Optimus - Consola Interactiva de Motores
echo ==========================================================
echo  Iniciando Consola de Comandos de Motores
echo  Topic: /motor_pwms
echo ==========================================================
wsl bash -l -c "cd '$(wslpath '%~dp0..')' && source /opt/ros/jazzy/setup.bash && source install/setup.bash && python3 tools/motor_terminal.py"
pause
