module mixed_test (
    input  logic       clk,
    input  logic       rst,
    input  logic       enable,
    input  logic       mode,
    input  logic [3:0] data_in,

    output logic [3:0] count,
    output logic       status,

    output logic [3:0] debug_value,
    output logic [3:0] data_copy,
    output logic       other_value
);

    // =========================================================
    // RELATED LOGIC 1: Counter
    // =========================================================
    always_ff @(posedge clk) begin
        if (rst)
            count <= 4'b0000;
        else if (enable)
            count <= count + 4'b0001;
    end


    // =========================================================
    // RELATED LOGIC 2: Status depends on count
    // =========================================================
    always_comb begin
        if (count == 4'b1111)
            status = 1'b1;
        else
            status = 1'b0;
    end


    // =========================================================
    // UNRELATED LOGIC 1
    // =========================================================
    always_ff @(posedge clk) begin
        if (rst)
            debug_value <= 4'b0000;
        else
            debug_value <= data_in + 4'b0010;
    end


    // =========================================================
    // UNRELATED LOGIC 2
    // =========================================================
    always_ff @(posedge clk) begin
        if (rst)
            data_copy <= 4'b0000;
        else
            data_copy <= data_in;
    end


    // =========================================================
    // UNRELATED LOGIC 3
    // =========================================================
    always_comb begin
        other_value = data_in ^ 4'b1010;
    end

endmodule