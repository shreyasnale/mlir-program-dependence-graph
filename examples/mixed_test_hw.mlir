module {
  hw.module @mixed_test(in %clk : i1, in %rst : i1, in %enable : i1, in %mode : i1, in %data_in : i4, out count : i4, out status : i1, out debug_value : i4, out data_copy : i4, out other_value : i1) {
    %true = hw.constant true
    %c2_i4 = hw.constant 2 : i4
    %c-1_i4 = hw.constant -1 : i4
    %c1_i4 = hw.constant 1 : i4
    %c0_i4 = hw.constant 0 : i4
    %0 = comb.add %count, %c1_i4 : i4
    %1 = comb.xor %rst, %true : i1
    %2 = comb.and %enable, %1 : i1
    %3 = comb.mux %2, %0, %c0_i4 : i4
    %4 = seq.to_clock %clk
    %5 = comb.or %rst, %enable : i1
    %6 = comb.mux bin %5, %3, %count : i4
    %count = seq.firreg %6 clock %4 : i4
    %7 = comb.icmp eq %count, %c-1_i4 : i4
    %8 = comb.add %data_in, %c2_i4 : i4
    %9 = comb.mux %1, %8, %c0_i4 : i4
    %debug_value = seq.firreg %9 clock %4 : i4
    %10 = comb.mux %rst, %c0_i4, %data_in : i4
    %data_copy = seq.firreg %10 clock %4 : i4
    %11 = comb.extract %data_in from 0 : (i4) -> i1
    hw.output %count, %7, %debug_value, %data_copy, %11 : i4, i1, i4, i4, i1
  }
}
