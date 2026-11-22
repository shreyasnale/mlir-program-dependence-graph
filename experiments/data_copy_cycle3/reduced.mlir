module {
  hw.module @mixed_test(in %clk : i1, in %rst : i1, in %data_in : i4, out data_copy : i4) {
    %c0_i4 = hw.constant 0 : i4
    %4 = seq.to_clock %clk
    %10 = comb.mux %rst, %c0_i4, %data_in : i4
    %data_copy = seq.firreg %10 clock %4 : i4
    hw.output %data_copy : i4
  }
}
