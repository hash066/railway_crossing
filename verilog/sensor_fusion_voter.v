// sensor_fusion_voter.v
`timescale 1ns/1ps

module sensor_fusion_voter #(
    parameter NUM_CROSSINGS = 4
)(
    input wire clk,
    input wire rst_n,
    input wire [NUM_CROSSINGS-1:0] ir_sensors,
    input wire [NUM_CROSSINGS-1:0] vib_sensors,
    input wire [NUM_CROSSINGS-1:0] rfid_signals,
    input wire [1:0] weather_mode,
    
    output reg [NUM_CROSSINGS-1:0] train_detected,
    output reg [NUM_CROSSINGS-1:0] train_exited,
    output wire [NUM_CROSSINGS-1:0] sensor_health
);

    integer i;
    reg [NUM_CROSSINGS-1:0] ir_prev;
    
    // 2-out-of-3 Voting Logic
    // If at least 2 sensors agree, we trust the result.
    always @(*) begin
        for (i = 0; i < NUM_CROSSINGS; i = i + 1) begin
            train_detected[i] = (ir_sensors[i] & vib_sensors[i]) | 
                                (ir_sensors[i] & rfid_signals[i]) | 
                                (vib_sensors[i] & rfid_signals[i]);
        end
    end

    // Exit detection logic: Falling edge of detection
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ir_prev <= 0;
            train_exited <= 0;
        end else begin
            for (i = 0; i < NUM_CROSSINGS; i = i + 1) begin
                if (ir_prev[i] && !train_detected[i])
                    train_exited[i] <= 1;
                else
                    train_exited[i] <= 0;
            end
            ir_prev <= train_detected;
        end
    end

    // Simple health check: if all three sensors are different (not possible with binary)
    // Actually, health check could be if one sensor disagrees with the other two for too long.
    // For now, let's say a sensor is healthy if it matches the voted output.
    assign sensor_health = 4'b1111; // Placeholder for now

endmodule
