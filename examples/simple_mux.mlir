module {
  hw.module @up_down_counter(in %clk : i1, in %reset : i1, in %enable : i1, in %up_down : i1, out count : i4) {
    %true = hw.constant true
    %c-1_i4 = hw.constant -1 : i4
    %c1_i4 = hw.constant 1 : i4
    %c0_i4 = hw.constant 0 : i4
    %0 = comb.add %count, %c1_i4 : i4
    %1 = comb.add %count, %c-1_i4 : i4
    %2 = comb.xor %reset, %true : i1
    %3 = comb.and %enable, %2 : i1
    %4 = comb.and %up_down, %3 : i1
    %5 = comb.mux %4, %0, %c0_i4 : i4
    %6 = comb.xor %up_down, %true : i1
    %7 = comb.and %6, %3 : i1
    %8 = comb.mux %7, %1, %5 : i4
    %9 = seq.to_clock %clk
    %10 = comb.or %reset, %enable : i1
    %11 = comb.mux bin %10, %8, %count : i4
    %count = seq.firreg %11 clock %9 : i4
    hw.output %count : i4
  }
}
