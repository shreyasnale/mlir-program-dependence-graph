module mixed_test(
    input        clk,
    input        rst,
    input        enable,
    input        mode,
    input  [3:0] data_in,
    output [3:0] data_copy
);

  reg [3:0] data_copy_0;

  always @(posedge clk)
    data_copy_0 <= rst ? 4'h0 : data_in;

  assign data_copy = data_copy_0;

endmodule
