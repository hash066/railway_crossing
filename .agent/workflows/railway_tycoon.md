---
description: Run the Verilog Railway Tycoon game simulation
---

This workflow compiles and runs the Verilog simulation of the Railway Tycoon game.

1. Ensure Icarus Verilog is installed (C:\iverilog\bin should exist).
2. Compile the design and testbench.
// turbo
C:\iverilog\bin\iverilog -g2012 -o game.vvp verilog/railway_system_top.v verilog/railway_controller_main.v verilog/sensor_fusion_voter.v verilog/train_speed_estimator.v verilog/statistics_engine.v tests/testbench_game_runner.v
3. Run the simulation.
// turbo
C:\iverilog\bin\vvp game.vvp
4. View the results in the terminal.
5. (Optional) Open game.vcd in GTKWave to see waveforms.
