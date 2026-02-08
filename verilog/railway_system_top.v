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
    output [7:0] debug_led,
    output [7:0] efficiency_score_out,
    output [11:0] crossing_states_out
);

// Internal signals
wire [3:0] train_detected_fused;
wire [3:0] train_exit_fused;
wire [3:0] sensor_health;
wire [31:0] safety_violations;
wire [31:0] total_delay;
wire [7:0] current_efficiency;

// Instantiate sensor fusion
sensor_fusion_voter #(.NUM_CROSSINGS(4)) sensor_fusion (
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

// Instantiate main controller
railway_controller_main #(.NUM_CROSSINGS(4)) main_ctrl (
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
    
    .crossing_states(crossing_states_out),
    .barrier_faults(),
    .light_faults()
);

// Instantiate speed estimator
train_speed_estimator #(.NUM_CROSSINGS(4)) speed_est (
    .clk(clk_50mhz),
    .rst_n(rst_n),
    .train_detected(train_detected_fused),
    .train_exited(train_exit_fused),
    .speed_val(),
    .speed_valid()
);

// Instantiate statistics engine
statistics_engine #(.NUM_CROSSINGS(4)) stats_eng (
    .clk(clk_50mhz),
    .rst_n(rst_n),
    .train_presence(train_detected_fused),
    .barrier_state(barrier_down),
    .emergency_active(emergency_global),
    .total_delay_cycles(total_delay),
    .safety_violations(safety_violations),
    .efficiency_score(current_efficiency)
);

assign efficiency_score_out = current_efficiency;

// Debug LEDs: show detection and top bits of efficiency
assign debug_led = {train_detected_fused, current_efficiency[7:4]};

endmodule 
