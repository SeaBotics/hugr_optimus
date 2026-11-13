@echo off
setlocal
if "%~1"=="" (
    echo ==========================================================
    echo  Hugr Optimus - Send Destination Helper
    echo ==========================================================
    echo  Usage examples:
    echo    send_destination.bat --x 15.0 --y 20.0
    echo    send_destination.bat --lat 58.33425 --lon 8.57845
    echo    send_destination.bat --cancel
    echo ==========================================================
    exit /b 1
)

wsl bash -l -c "cd '$(wslpath '%~dp0..')' && source install/setup.bash && ros2 run hugr_autonomy send_destination %*"
