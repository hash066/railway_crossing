`timescale 1ns/1ps

module testbench_game_runner;
    reg clk;
    reg rst_n;
    reg [3:0] ir_sensor;
    reg [3:0] vib_sensor;
    reg [3:0] rfid_valid;
    reg emergency_global;
    reg [1:0] weather_mode;
    
    wire [3:0] barrier_down;
    wire [3:0] red_light;
    wire [3:0] yellow_light;
    wire [3:0] alarm_sound;
    wire [7:0] debug_led;
    wire [7:0] efficiency_score;
    wire [11:0] crossing_states;

    // Instantiate UUT
    railway_system_top uut (
        .clk_50mhz(clk),
        .rst_n(rst_n),
        .ir_sensor(ir_sensor),
        .vib_sensor(vib_sensor),
        .rfid_valid(rfid_valid),
        .emergency_global(emergency_global),
        .weather_mode(weather_mode),
        .barrier_down(barrier_down),
        .red_light(red_light),
        .yellow_light(yellow_light),
        .alarm_sound(alarm_sound),
        .debug_led(debug_led),
        .efficiency_score_out(efficiency_score),
        .crossing_states_out(crossing_states)
    );

    // Clock generation
    initial clk = 0;
    always #10 clk = ~clk;

    // Simulation tasks
    task send_train(input integer crossing, input integer duration);
    begin
        $display("[%0d][TRAIN] Entering Crossing %0d", $time, crossing);
        ir_sensor[crossing] = 1;
        vib_sensor[crossing] = 1;
        rfid_valid[crossing] = 1;
        repeat (duration) @(posedge clk);
        ir_sensor[crossing] = 0;
        vib_sensor[crossing] = 0;
        rfid_valid[crossing] = 0;
        $display("[%0d][TRAIN] Exited Crossing %0d", $time, crossing);
        repeat (100) @(posedge clk);
    end
    endtask

    initial begin
        // Initialize
        rst_n = 0;
        ir_sensor = 0;
        vib_sensor = 0;
        rfid_valid = 0;
        emergency_global = 0;
        weather_mode = 0;
        
        $display("========================================");
        $display("   VERILOG RAILWAY TYCOON - LEVEL 1");
        $display("========================================");
        
        #100 rst_n = 1;
        
        // Level 1: Normal Train
        send_train(0, 500);
        send_train(1, 400);
        
        $display("[SCORE] Level 1 Complete. Efficiency: %0d%%", efficiency_score);
        
        // Level 2: The Storm (One sensor fails)
        $display("\n========================================");
        $display("   LEVEL 2 - THE STORM (Sensor Failure)");
        $display("========================================");
        weather_mode = 2'b10; // Storm mode
        
        // Train comes, but IR sensor is broken (stuck 0)
        $display("[DANGER] IR Sensor Failure at Crossing 2");
        ir_sensor[2] = 0; // Broken
        vib_sensor[2] = 1;
        rfid_valid[2] = 1;
        repeat (600) @(posedge clk);
        ir_sensor[2] = 0;
        vib_sensor[2] = 0;
        rfid_valid[2] = 0;
        $display("[TRAIN] Exited Crossing 2 (Handled by redundancy)");
        
        $display("[SCORE] Level 2 Complete. Efficiency: %0d%%", efficiency_score);

        // Level 3: Rush Hour
        $display("\n========================================");
        $display("   LEVEL 3 - RUSH HOUR (Parallel Trains)");
        $display("========================================");
        
        fork
            send_train(0, 800);
            #1000 send_train(1, 600);
            #2000 send_train(2, 900);
        join
        
        #2000;
        $display("========================================");
        $display("GAME OVER - Final Score: %0d%%", efficiency_score);
        if (efficiency_score > 80)
            $display("RANK: S - Hardware Tycoon!");
        else
            $display("RANK: B - Keep Optimizing!");
        $display("========================================");
        
        $finish;
    end

    initial begin
        $dumpfile("game.vcd");
        $dumpvars(0, testbench_game_runner);
    end

endmodule
