module {
  hw.module @temporal_chain(in %clk : i1, in %rst : i1, in %data_in : i4, out output_value : i4) {
    %true = hw.constant true
    %c1_i4 = hw.constant 1 : i4
    %c0_i4 = hw.constant 0 : i4
    %0 = comb.add %data_in, %c1_i4 : i4
    %1 = comb.add %reg_a, %c1_i4 : i4
    %2 = comb.add %reg_b, %c1_i4 : i4
    %3 = comb.xor %rst, %true : i1
    %4 = comb.mux %3, %0, %c0_i4 : i4
    %5 = comb.mux %3, %1, %c0_i4 : i4
    %6 = comb.mux %3, %2, %c0_i4 : i4
    %7 = seq.to_clock %clk
    %reg_a = seq.firreg %4 clock %7 : i4
    %reg_b = seq.firreg %5 clock %7 : i4
    %reg_c = seq.firreg %6 clock %7 : i4
    hw.output %reg_c : i4
  }
}
