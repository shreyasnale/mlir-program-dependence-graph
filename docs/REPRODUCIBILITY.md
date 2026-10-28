# Reproducibility Notes

## 1. Existing dependency-graph example

Run from the repository root:

```powershell
python .\src\pdg_from_mlir.py .\examples\simple_mux.mlir .\output\simple_mux.dot
```

If Graphviz is installed:

```powershell
dot -Tpng .\output\simple_mux.dot -o .\output\simple_mux.png
```

The script has no external Python package dependencies according to the current `requirements.txt`. Graph rendering requires the Graphviz `dot` executable.

## 2. Generate hardware IR from SystemVerilog

The project notes record a local Windows installation at `F:\Projects\circt\build\bin`. Adjust all paths for your setup.

For a source file `mixed_test.sv`, a typical frontend invocation from the working notes is:

```powershell
& "F:\Projects\circt\build\bin\circt-verilog.exe" --ir-hw .\mixed_test.sv -o .\mixed_test_hw.mlir
```

Confirm the exact options with your installed binary's `--help`, because CIRCT CLI options may differ by build/version.

## 3. V5 → V6 lowering and export

These commands are transcribed from the working notes and assume `mixed_test_reduced_v5.mlir` already exists:

```powershell
& "F:\Projects\circt\build\bin\circt-opt.exe" .\mixed_test_reduced_v5.mlir --lower-seq-to-sv -o .\mixed_test_reduced_v6_lowered.mlir
& "F:\Projects\circt\build\bin\circt-opt.exe" .\mixed_test_reduced_v6_lowered.mlir --export-verilog -o NUL > .\mixed_test_reduced_v6.sv
```

Inspect the generated SystemVerilog before compiling it. The historical line-extraction command below is brittle and must not be used blindly if the emitted file changes:

```powershell
Get-Content .\mixed_test_reduced_v6.sv |
    Select-Object -Skip 45 -First 41 |
    Set-Content .\mixed_test_reduced_v6_clean.sv
```

Prefer a stable generated module boundary or a checked-in, manually reviewed generated source file instead of relying on fixed line numbers.

## 4. Simulation comparison

The working notes use Icarus Verilog (`iverilog` and `vvp`) with three inputs: original RTL, reduced generated SystemVerilog, and a comparison testbench.

```powershell
iverilog -g2012 -s tb_compare -o .\v6_compare.vvp .\mixed_test.sv .\mixed_test_reduced_v6_clean.sv .\tb_compare.sv
vvp .\v6_compare.vvp
```

Recorded output in the working notes was PASS for the tested sequences. That is simulation evidence only. A reproducible result requires publishing the exact input files, testbench, tool versions, full output log, and the test sequences or stimulus-generation logic.

## 5. Record each experiment

For each result, record:
- Git commit and operating system
- CIRCT/MLIR build version or commit
- Icarus Verilog version
- Input RTL and exact intermediate/final MLIR
- Slicing criterion and temporal horizon
- Exact commands
- Original and retained operation counting rule
- Full stdout/stderr or testbench transcript
- Known limitations and whether the result is manually reviewed, simulated, or formally proven

## Current repository completeness

The current repository snapshot does not contain the exact V4/V5 scripts, `mixed_test_hw.mlir`, reduced V4/V5 MLIR, `mixed_test.sv`, generated reduced SystemVerilog, or `tb_compare.sv`. Therefore this file documents commands preserved in project notes; it does not claim that the V4–V6 experiment is currently reproducible from a fresh clone.
