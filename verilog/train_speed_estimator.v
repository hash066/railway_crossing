// train_speed_estimator.v
`timescale 1ns/1ps

module train_speed_estimator #(
    parameter NUM_CROSSINGS = 4,
    parameter TRAIN_LENGTH_BITS = 16 // Assume a constant train length for speed calc
)(
    input wire clk,
    input wire rst_n,
    input wire [NUM_CROSSINGS-1:0] train_detected,
    input wire [NUM_CROSSINGS-1:0] train_exited,
    
    output reg [31:0] speed_val [0:NUM_CROSSINGS-1],
    output reg [NUM_CROSSINGS-1:0] speed_valid
);

    reg [31:0] timer [0:NUM_CROSSINGS-1];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < NUM_CROSSINGS; i = i + 1) begin
                timer[i] <= 0;
                speed_val[i] <= 0;
                speed_valid[i] <= 0;
            end
        end else begin
            for (i = 0; i < NUM_CROSSINGS; i = i + 1) begin
                if (train_detected[i]) begin
                    timer[i] <= timer[i] + 1;
                    speed_valid[i] <= 0;
                end else if (train_exited[i]) begin
                    // Speed calculation: (Length Constant) / timer
                    // To avoid division in hardware, we just output the timer as inverse speed
                    // or use a pre-calculated constant.
                    // speed = 1000000 / timer (scaled)
                    if (timer[i] > 0)
                        speed_val[i] <= 1000000 / timer[i];
                    else
                        speed_val[i] <= 0;
                    
                    speed_valid[i] <= 1;
                    timer[i] <= 0;
                end else begin
                    speed_valid[i] <= 0;
                    timer[i] <= 0;
                end
            end
        end
    end

endmodule
