// railway_system_top.v
`timescale 1ns/1ps

module railway_system_top(
    input clk_50mhz,
    input rst_n,
    input [3:0] ir_sensor,
    input [3:0] vib_sensor,
    input [3:0] rfid_valid,
    input emergency_global,
    input [1:0] weather_mode,
    
    output [3:0] barrier_down,
    output [3:0] red_light,
    output [3:0] yellow_light,
    output [3:0] alarm_sound,
    output [7:0] debug_led
);

// Internal signals
wire [3:0] train_detected_fused;
wire [3:0] train_exit_fused;
wire [3:0] sensor_health;
wire [31:0] system_stats;
wire uart_tx;

// Instantiate main controller
railway_controller_main main_ctrl (
    .clk(clk_50mhz),
    .rst_n(rst_n),
    .train_detected(train_detected_fused),
    .train_exited(train_exit_fused),
    .emergency_global(emergency_global),
    .weather_mode(weather_mode),
    .sensor_health(sensor_health),
    
    .barrier_down(barrier_down),
    .red_light(red_light),
    .yellow_light(yellow_light),
    .alarm_sound(alarm_sound),
    
    .crossing_states(),
    .barrier_faults(),
    .light_faults()
);

// Instantiate sensor fusion
sensor_fusion_voter sensor_fusion (
    .clk(clk_50mhz),
    .rst_n(rst_n),
    .ir_sensors(ir_sensor),
    .vib_sensors(vib_sensor),
    .rfid_signals(rfid_valid),
    .weather_mode(weather_mode),
    .train_detected(train_detected_fused),
    .train_exited(train_exit_fused),
    .sensor_health(sensor_health)
);

// Debug LEDs
assign debug_led = {train_detected_fused, weather_mode, emergency_global, 1'b1};

endmodule 
