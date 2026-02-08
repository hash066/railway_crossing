@echo off
set IVERILOG_PATH=C:\iverilog\bin
echo ========================================
echo   RAILWAY TYCOON SIMULATION STARTER
echo ========================================
echo.
echo [1/2] Compiling Hardware Logic...
%IVERILOG_PATH%\iverilog -g2012 -o game.vvp verilog/railway_system_top.v verilog/railway_controller_main.v verilog/sensor_fusion_voter.v verilog/train_speed_estimator.v verilog/statistics_engine.v verilog/railway_system_tb.v
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [2/2] Running Simulation...
%IVERILOG_PATH%\vvp game.vvp
echo.
echo [COMPLETE] game.vcd generated. Open in GTKWave for waveforms.
pause
