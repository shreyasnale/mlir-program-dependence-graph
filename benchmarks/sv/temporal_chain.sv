module temporal_chain (
    input  logic       clk,
    input  logic       rst,
    input  logic [3:0] data_in,
    output logic [3:0] output_value
);

    logic [3:0] reg_a;
    logic [3:0] reg_b;
    logic [3:0] reg_c;

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_a <= 4'd0;
            reg_b <= 4'd0;
            reg_c <= 4'd0;
        end
        else begin
            reg_a <= data_in + 4'd1;
            reg_b <= reg_a + 4'd1;
            reg_c <= reg_b + 4'd1;
        end
    end

    assign output_value = reg_c;

endmodule