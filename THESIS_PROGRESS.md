# Thesis Progress Log

Project: Cycle-aware backward slicing for CIRCT/MLIR hardware descriptions  
Repository: [mlir-program-dependence-graph](https://github.com/shreyasnale/mlir-program-dependence-graph)

## Purpose

This file records thesis implementation milestones, experiments, observed results, and open questions. Entries distinguish between code that runs and behavior that has been validated.

## Current baseline: Steps 1–6

### Step 1 — Create a small RTL test case
- **Goal:** Start with a circuit whose behavior and dependencies are easy to inspect.
- **Work:** Created a SystemVerilog counter with clock, reset, enable, and a 4-bit count output.
- **Result:** The counter is the initial test design used in the local prototype.
- **Status:** Implemented for the initial test case.

### Step 2 — Convert RTL to CIRCT/MLIR
- **Goal:** Work with a hardware-oriented intermediate representation.
- **Work:** Used `circt-verilog` with `--ir-hw` to generate `counter_hw.mlir`.
- **Result:** The generated IR contains combinational operations and a sequential register operation, including `comb.add`, `comb.mux`, and `seq.firreg`.
- **Status:** Generated successfully for the counter example.

### Step 3 — Extract SSA dependencies
- **Goal:** Determine which SSA values are used by each operation.
- **Work:** Implemented Python parsing logic to extract operation results and operand references from MLIR text.
- **Result:** The prototype prints initial result-to-operand relationships.
- **Status:** Prototype implemented; parser robustness needs further testing.

### Step 4 — Add dependency types and cycle offsets
- **Goal:** Represent initial data/control/state relationships and their temporal interpretation.
- **Work:** Added heuristic labels such as `DATA`, `CONTROL`, and `STATE`; combinational operations use offset 0 and `seq.firreg` data dependencies use offset -1. The clock operand is excluded from the data/state slice.
- **Result:** A typed dependency graph is produced for the counter IR.
- **Status:** Initial model only; operation semantics and offset conventions must be validated.

### Step 5 — Implement backward slicing
- **Goal:** Find values that may influence a chosen signal at a selected cycle within a cycle horizon.
- **Work:** Added a worklist of (signal, cycle) pairs, a visited set, and a minimum-cycle boundary.
- **Result:** The traversal runs and produces slices for different criterion cycles.
- **Status:** Prototype runs; correctness, completeness, and minimality are not yet established.

### Step 6 — Integrate the prototype
- **Goal:** Combine MLIR parsing, dependency construction, temporal labels, and backward traversal.
- **Work:** Integrated the workflow in `cycle_slice_auto.py` for the counter example.
- **Result:** The script prints visited signal/cycle pairs and a final slice.
- **Status:** End-to-end prototype runs on the initial example; this is not yet proof of semantic correctness.

## Current limitations and risks

- The parser uses text/regular-expression heuristics and may not support all valid MLIR forms.
- Operand roles, especially mux control/data operands, must be checked against CIRCT operation semantics.
- Sequential behavior, reset/enable logic, and the cycle-offset convention need manual validation.
- The current counter example is insufficient to demonstrate generality.
- Research novelty must be assessed through a focused literature review; no novelty claim is made here.

## Next milestone — Step 7: Validate against a manual reference

1. Write down the expected dependencies for the counter from the RTL and generated IR.
2. Verify each operation's operand roles and register-update semantics against CIRCT documentation or verified examples.
3. Compare the manual reference with the script output for selected criterion signals and cycles.
4. Record mismatches, fix the implementation, and rerun the tests.
5. Add at least one additional small combinational or sequential test case after the counter baseline is understood.

## Repeatable GitHub update workflow

For every milestone:

1. Make a focused code or documentation change.
2. Run the relevant command/test and preserve the actual output.
3. Update this log with **Goal**, **Changes**, **Validation**, **Outcome**, and **Open issues**.
4. Inspect the diff and ensure no credentials, local absolute paths, build artifacts, or unrelated files are included.
5. Commit with a concise message, for example `test: validate counter slice against manual reference`.
6. Push the commit and verify it appears on GitHub.

## Entry template

Copy this section for each new milestone:

### Step N — Short title
- **Goal:**
- **Changes:**
- **Validation command/test:**
- **Observed result:**
- **Status:** Not started / In progress / Implemented / Validated
- **Open issues:**
- **Next action:**


## Later experiments — V4 to V6

The working notes for V4–V6 are summarized in [docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md), with commands in [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md). The exact V4/V5 scripts and V6 RTL/testbench artifacts are not yet in this repository snapshot, so these measurements are labeled as working-note-reported rather than independently reproduced.

### V4 — reduction experiment
- **Reported files:** `reduction_analysis_v4.py`, `mixed_test_hw.mlir`, `mixed_test_reduced_v4.mlir`.
- **Observed result:** Not confirmed from the available repository snapshot.
- **Status:** Historical experiment noted; artifacts/results need upload and verification.

### V5 — mixed sequential/combinational reduction
- **Reported criterion:** RTL `<status,3>` mapped to SSA `<%7,3>`.
- **Reported counts:** 20 original MLIR operations, 13 retained, 7 removed (35% of counted operations).
- **Interpretation:** Operation-count metric only; not a gate-area, power or timing estimate.
- **Status:** Working-note-reported; scripts and input/output MLIR are not yet in this repository snapshot.

### V6 — lower and simulate
- **Reported workflow:** lower reduced MLIR with `--lower-seq-to-sv`, export SystemVerilog, then compile and simulate the original and reduced designs with Icarus Verilog.
- **Reported result:** PASS for status outputs over the test sequences exercised by the recorded testbench.
- **Limitation:** Simulation agreement for tested sequences is not a formal equivalence proof.
- **Status:** Working-note-reported; exact generated files and testbench still need to be uploaded for reproduction.

### Next concrete task
Upload the actual V4/V5 scripts, helper modules, source RTL, intermediate MLIR, reduced MLIR, reduced generated SystemVerilog and `tb_compare.sv`. Then rerun from a clean checkout and replace note-reported results with verified results and logs.
