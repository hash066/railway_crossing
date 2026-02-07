 // railway_controller_main.v
module railway_controller_main #(
    parameter NUM_CROSSINGS = 4
)(
    input wire clk,
    input wire rst_n,
    input wire [NUM_CROSSINGS-1:0] train_detected,
    input wire [NUM_CROSSINGS-1:0] train_exited,
    input wire emergency_global,
    input wire [1:0] weather_mode,
    input wire [NUM_CROSSINGS-1:0] sensor_health,
    
    output reg [NUM_CROSSINGS-1:0] barrier_down,
    output reg [NUM_CROSSINGS-1:0] red_light,
    output reg [NUM_CROSSINGS-1:0] yellow_light,
    output reg [NUM_CROSSINGS-1:0] alarm_sound,
    
    output wire [NUM_CROSSINGS*3-1:0] crossing_states,
    output wire [NUM_CROSSINGS-1:0] barrier_faults,
    output wire [NUM_CROSSINGS-1:0] light_faults
);

// State definitions
parameter [2:0] 
    IDLE        = 3'b000,
    WARNING     = 3'b001,
    COUNTDOWN   = 3'b010,
    BARRIER_DN  = 3'b011,
    TRAIN_PASS  = 3'b100,
    EMERGENCY   = 3'b110,
    MAINTENANCE = 3'b111;

reg [2:0] current_state [0:NUM_CROSSINGS-1];
reg [2:0] next_state [0:NUM_CROSSINGS-1];
reg [23:0] counters [0:NUM_CROSSINGS-1];
reg [7:0] countdowns [0:NUM_CROSSINGS-1];

// Initialize
integer i;
initial begin
    for (i = 0; i < NUM_CROSSINGS; i = i + 1) begin
        current_state[i] = IDLE;
        counters[i] = 0;
        countdowns[i] = 10;
    end
end

// State machines for each crossing
genvar j;
generate
    for (j = 0; j < NUM_CROSSINGS; j = j + 1) begin : crossing_fsms
        always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
                current_state[j] <= IDLE;
                counters[j] <= 0;
            end else begin
                current_state[j] <= next_state[j];
                counters[j] <= counters[j] + 1;
                
                if (current_state[j] == COUNTDOWN) begin
                    if (counters[j][4:0] == 5'b11111) begin
                        if (countdowns[j] > 0) 
                            countdowns[j] <= countdowns[j] - 1;
                    end
                end else if (current_state[j] == IDLE) begin
                    countdowns[j] <= 10;
                end
            end
        end
        
        always @(*) begin
            next_state[j] = current_state[j];
            
            if (emergency_global) begin
                next_state[j] = EMERGENCY;
            end else begin
                case(current_state[j])
                    IDLE: if (train_detected[j]) next_state[j] = WARNING;
                    WARNING: if (counters[j][23:20] == 5) next_state[j] = COUNTDOWN;
                    COUNTDOWN: if (countdowns[j] == 0) next_state[j] = BARRIER_DN;
                    BARRIER_DN: if (counters[j][2:0] == 3) next_state[j] = TRAIN_PASS;
                    TRAIN_PASS: if (train_exited[j]) next_state[j] = IDLE;
                    EMERGENCY: if (!emergency_global) next_state[j] = IDLE;
                endcase
            end
        end
        
        always @(*) begin
            case(current_state[j])
                IDLE: begin
                    barrier_down[j] = 0;
                    red_light[j] = 0;
                    yellow_light[j] = 0;
                    alarm_sound[j] = 0;
                end
                WARNING: begin
                    barrier_down[j] = 0;
                    red_light[j] = 0;
                    yellow_light[j] = 1;
                    alarm_sound[j] = counters[j][22];
                end
                COUNTDOWN: begin
                    barrier_down[j] = 0;
                    red_light[j] = 1;
                    yellow_light[j] = 0;
                    alarm_sound[j] = counters[j][20];
                end
                BARRIER_DN: begin
                    barrier_down[j] = 1;
                    red_light[j] = 1;
                    yellow_light[j] = 0;
                    alarm_sound[j] = 1;
                end
                TRAIN_PASS: begin
                    barrier_down[j] = 1;
                    red_light[j] = 1;
                    yellow_light[j] = 0;
                    alarm_sound[j] = 0;
                end
                EMERGENCY: begin
                    barrier_down[j] = 0;
                    red_light[j] = 1;
                    yellow_light[j] = counters[j][21];
                    alarm_sound[j] = 1;
                end
                default: begin
                    barrier_down[j] = 0;
                    red_light[j] = 0;
                    yellow_light[j] = 0;
                    alarm_sound[j] = 0;
                end
            endcase
        end
        
        assign crossing_states[j*3 +: 3] = current_state[j];
    end
endgenerate

assign barrier_faults = 0;
assign light_faults = 0;

endmodule