# Development History: From Initial PDG to V4–V6

This document preserves the progression recorded in the thesis notes and extends it with the later slicing experiments. It distinguishes repository-inspected artifacts from results reported in working notes.

## Foundation — graph generation and initial examples

### Repository state inspected
The repository currently includes:
- `src/pdg_from_mlir.py`: Python text parser for a limited set of MLIR operations.
- `examples/simple_mux.mlir`: a small counter-like circuit with muxes, arithmetic, clock conversion, and a sequential register.
- `output/simple_mux.dot` and PNG renderings.
- `THESIS_PROGRESS.md`: a milestone log for Steps 1–6.

### Initial generator behavior
The script scans input text for a list of known operations, maps SSA results to producer nodes, and creates data edges. For `comb.mux`, it heuristically treats the first operand as the control operand and draws it as a control edge.

### Known constraints
This is a limited text/regex-based prototype, not a full MLIR parser. The code should be validated for operation-specific operand roles, clock handling, scoping, block arguments, and other MLIR syntax before relying on it for a general dependence analysis.

## Steps 1–6 — baseline prototype

The existing `THESIS_PROGRESS.md` records the initial work as:
1. Create a small RTL counter test.
2. Convert the RTL to CIRCT/MLIR using `circt-verilog` and `--ir-hw`.
3. Extract SSA results and operands.
4. Add initial data/control/state edge labels and cycle-offset assumptions.
5. Implement a worklist-based backward traversal over (signal, cycle) pairs.
6. Integrate the workflow in `cycle_slice_auto.py` for an initial counter example.

The progress log labels this as a working prototype and explicitly notes that correctness, completeness, and minimality have not yet been established. Some scripts named in the historical progress log are not present in the repository snapshot inspected for this documentation update.

## Step 7 — manual-reference validation (planned/ongoing)

The existing progress log proposes writing down expected RTL dependencies, checking operand roles and register semantics, comparing with script output, recording mismatches, and adding another test case. The available repository snapshot does not itself establish that all these checks have been completed.

## V4 — reduction analysis experiment

Working notes identify a V4 script named `reduction_analysis_v4.py`, with input `mixed_test_hw.mlir` and output `mixed_test_reduced_v4.mlir`. The exact V4 output and quantitative results were not available for independent verification during this repository review.

**Status in this documentation:** recorded as a historical experiment, not a verified result. Add the script, input/output artifacts, exact command, and captured console output before publishing V4 measurements.

## V5 — mixed sequential/combinational reduction experiment

Working notes identify:
- Script: `reduction_analysis_v5.py`
- Input: `mixed_test_hw.mlir`
- Output: `mixed_test_reduced_v5.mlir`
- Related modules: `cycle_slice_auto_v2.py` and `output_mapping_v3.py`
- Criterion: RTL `<status,3>`, mapped to SSA `<%7,3>`

The recorded experiment reports:
- Original counted MLIR operations: 20
- Retained counted MLIR operations: 13
- Counted operations removed: 7
- Potential reduction in that operation count: 35.00%

The notes list semantic retained values and one additional structural clock dependency. These figures come from the working notes and are not independently reproducible from the current repository snapshot, because the named scripts and input/output files are not present here.

### Interpretation
The 35% figure is based solely on the stated count of MLIR operations. It is not a measurement of physical gate count, silicon area, power, or timing. The retained operation set and the cycle interpretation need validation against CIRCT semantics and RTL behavior.

## V6 — lower the reduced IR and compare simulation outputs

The working notes record this lowering command on Windows:

```powershell
& "F:\Projects\circt\build\bin\circt-opt.exe" .\mixed_test_reduced_v5.mlir --lower-seq-to-sv -o .\mixed_test_reduced_v6_lowered.mlir
```

The notes then record exporting SystemVerilog:

```powershell
& "F:\Projects\circt\build\bin\circt-opt.exe" .\mixed_test_reduced_v6_lowered.mlir --export-verilog -o NUL > .\mixed_test_reduced_v6.sv
```

One recorded extraction command for a generated file layout was:

```powershell
Get-Content .\mixed_test_reduced_v6.sv |
    Select-Object -Skip 45 -First 41 |
    Set-Content .\mixed_test_reduced_v6_clean.sv
```

This line-range extraction is layout-dependent; inspect the generated file rather than assuming the same line numbers apply to other CIRCT versions.

The recorded verification used `iverilog` and `vvp` in `v6_verification`, with original RTL, reduced generated SystemVerilog, and `tb_compare.sv`:

```powershell
iverilog -g2012 -s tb_compare -o .\v6_compare.vvp .\mixed_test.sv .\mixed_test_reduced_v6_clean.sv .\tb_compare.sv
vvp .\v6_compare.vvp
```

The saved result in the working notes was:

```text
V6 RESULT: PASS
Original and reduced status outputs match.
```

### Interpretation and limitations
This records output agreement for the sequences exercised by that testbench, not a formal equivalence proof over every input sequence. To reproduce it, commit the exact RTL, reduced file-generation inputs, testbench, complete console log, and tool versions. The notes also identify unused `mode` and `data_in` ports as possible cleanup work.

## Current gap between the repository and working notes

The repository snapshot reviewed for this update does **not** contain the named V4–V6 scripts, `mixed_test_hw.mlir`, generated reduced MLIR files, `mixed_test.sv`, or `tb_compare.sv`. The history above documents the work as recorded in the conversation notes, but the artifacts still need to be uploaded to make the experiments self-contained and reproducible.

## Next actions

1. Add the original mixed RTL and exact generated HW/Comb/Seq IR used by the experiments.
2. Add the V4/V5 Python scripts and helper modules, preserving actual source code rather than reconstructed substitutes.
3. Add V4/V5 reduced IR outputs and exact commands/logs.
4. Add the original and reduced SystemVerilog, testbench, and V6 simulation transcript.
5. Rerun the pipeline and replace the recorded outputs only with actual new results.
6. Validate cycle offsets and dependence rules against CIRCT operation semantics and a manually derived reference.
7. Only after a focused literature review, make a qualified novelty statement.

## Evidence convention

- **Repository-inspected:** artifact exists in the public repository reviewed.
- **Working-note-reported:** described in project notes, but artifacts/results were not independently reproduced here.
- **Planned/ongoing:** next step, not represented as completed.
