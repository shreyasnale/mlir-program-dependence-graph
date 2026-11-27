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

### Step 8 — Fix dangling-SSA bug in reduced-MLIR generation and validate cycle-bounded reduction
- **Goal:** Fix the cases where `generate_reduced_mlir` kept an operation (usually a `seq.firreg`) that referenced an operand whose defining operation had been cut by the cycle bound, producing MLIR that failed `circt-opt` validation. Then confirm cycle-bounded slicing actually reduces finite-depth logic and correctly does *not* reduce feedback logic.
- **Changes:**
  - `src/cycle_slicing/cycle_slice_tool_v4_portfix.py`: in `generate_reduced_mlir`, any SSA value used by a retained operation but no longer produced within the retained set is promoted to a new module input port (same SSA name, inferred type from the original IR) instead of being left dangling.
  - Added two benchmark designs: `benchmarks/mlir/mixed_test_hw.mlir` / `benchmarks/sv/mixed_test.sv` (feedback counter `count`, plus `data_copy`, `debug_value`, `status`) and `benchmarks/mlir/temporal_chain_hw.mlir` / `benchmarks/sv/temporal_chain.sv` (3-stage register chain `data -> reg_a -> reg_b -> reg_c -> output_value`, no feedback).
- **Validation command/test:** `python cycle_slice_tool_v4_portfix.py --mlir <file> --output <signal> --cycle <k>` for every cycle 0–5 on both designs, checked against real `circt-opt` (not a hand-rolled checker).
- **Observed result:**

  `temporal_chain` / `output_value` (14 original ops, depth 3, no feedback):

  | cycle | ops kept | reduction |
  |---|---|---|
  | 0 | 2 | 85.71% |
  | 1 | 9 | 35.71% |
  | 2 | 12 | 14.29% |
  | 3 | 14 | 0% |
  | 4 | 14 | 0% |
  | 5 | 14 | 0% |

  `mixed_test` / `count` (20 original ops, register with feedback):

  | cycle | ops kept | reduction |
  |---|---|---|
  | 0 | 2 | 90% |
  | 1 | 11 | 45% |
  | 3 | 11 | 45% |

  All cases: `CIRCT VALIDATION: PASS`, `CIRCT SV generation: PASS`.
- **Status:** Implemented, validated against `circt-opt`.
- **Open issues:**
  - `seq.firreg ... reset sync %rst, %val` (reset as an explicit register operand) is not yet followed as a dependency — only designs where `circt-verilog` lowers reset into a `comb.mux` are correctly handled.
  - Only operation-count reduction and syntactic (`circt-opt`) validity are shown. Behavioral equivalence between original and reduced design up to cycle k (e.g. via a miter + `circt-bmc`, or simulation) is not yet implemented — this is the next milestone.
  - Parser is still text/regex-based (`re.findall` over MLIR text), not CIRCT's own SSA/operation API, per the exposé's stated methodology.
- **Next action:** Implement a correctness check (miter comparing original vs. reduced design, formal via `circt-bmc -b k` or simulation) so that reduction results can be reported alongside a behavior-preservation guarantee, not operation counts alone.
