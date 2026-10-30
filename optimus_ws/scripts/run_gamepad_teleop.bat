@echo off
title Hugr Optimus - Control Remoto con Mando (Windows -> ROS 2)
echo ================================================================================
echo        SeaBotics Hugr Optimus - Teleoperacion con Mando Xbox / DirectInput
echo ================================================================================
echo.

cd /d "%~dp0.."

echo [1/2] Iniciando receptor de ROS 2 en WSL2 (Topic /motor_pwms)...
start /B wsl bash -l -c "cd '$(wslpath '%~dp0..')' && source /opt/ros/jazzy/setup.bash && source install/setup.bash && python3 tools/gamepad_ros_receiver.py"

echo [2/2] Esperando 2 segundos para asegurar inicio del receptor...
timeout /t 2 /nobreak >nul

echo [3/3] Iniciando lector del mando en Windows...
echo.
python tools\gamepad_teleop.py

echo.
echo Cerrando receptor en WSL2...
wsl bash -l -c "pkill -f gamepad_ros_receiver.py" >nul 2>&1
echo Listo.
pause
