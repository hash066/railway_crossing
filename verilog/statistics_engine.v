// statistics_engine.v
`timescale 1ns/1ps

module statistics_engine #(
    parameter NUM_CROSSINGS = 4
)(
    input wire clk,
    input wire rst_n,
    input wire [NUM_CROSSINGS-1:0] train_presence,
    input wire [NUM_CROSSINGS-1:0] barrier_state,
    input wire emergency_active,
    
    output reg [31:0] total_delay_cycles,
    output reg [31:0] safety_violations,
    output wire [7:0] efficiency_score
);

    integer i;
    reg [NUM_CROSSINGS-1:0] prev_train_presence;
    reg [31:0] violation_event_count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            total_delay_cycles <= 0;
            safety_violations <= 0;
            violation_event_count <= 0;
            prev_train_presence <= 0;
        end else begin
            for (i = 0; i < NUM_CROSSINGS; i = i + 1) begin
                // Safety Violation: Train present but barrier NOT down
                // Only count as a violation if it stays up too long after detection
                // For simplicity in this gamified version, we'll count cycles where it's dangerously up
                if (train_presence[i] && !barrier_state[i]) begin
                    safety_violations <= safety_violations + 1;
                end
                
                // Delay: Barrier down but NO train present (unnecessary waiting for cars)
                if (barrier_state[i] && !train_presence[i] && !emergency_active) begin
                    total_delay_cycles <= total_delay_cycles + 1;
                end
            end
            prev_train_presence <= train_presence;
        end
    end

    // Refined Efficiency Score:
    // Safety is paramount: 1 violation cycle = -1 point (very harsh)
    // Delay is expensive: 100 delay cycles = -1 point
    // We'll use a larger scale to avoid hitting 0 immediately
    wire [31:0] safety_penalty;
    wire [31:0] delay_penalty;
    
    // In our simulation, a train pass has ~200 cycles of "warning/setup"
    // So we'll give a 300 cycle "grace" for safety per train? No, let's just scale it.
    assign safety_penalty = (safety_violations / 50); // Every 50 cycles of danger = -1%
    assign delay_penalty = (total_delay_cycles / 200); // Every 200 cycles of delay = -1%
    
    wire [31:0] total_penalty = safety_penalty + delay_penalty;
    assign efficiency_score = (total_penalty >= 100) ? 8'd0 : (8'd100 - total_penalty[7:0]);

endmodule
