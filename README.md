# MLIR Program Dependence Graph Generator and Cycle-Aware Slicing

A research prototype for exploring data/control dependencies in CIRCT/MLIR hardware descriptions and backward, cycle-aware slicing of SystemVerilog designs.

> **Research status:** This is a prototype. Parsing and slicing rules still require validation against CIRCT operation semantics and reference RTL behavior. Reported operation counts are IR metrics, not hardware area or timing improvements.

## Current scope

- Parse a limited set of CIRCT/MLIR operations and associate SSA values with producer operations.
- Generate a simplified dependency graph with data dependencies and heuristic mux-control edges.
- Explore cycle-aware backward slicing across combinational and sequential logic.
- Lower reduced IR to SystemVerilog for simulation-based comparison.
- Keep implementation milestones, evidence, and limitations documented.

## Repository layout

```text
.
├── src/
│   └── pdg_from_mlir.py
├── examples/
│   └── simple_mux.mlir
├── output/
│   ├── simple_mux.dot
│   └── simple_mux.png
├── docs/
│   ├── DEVELOPMENT_HISTORY.md
│   └── REPRODUCIBILITY.md
├── THESIS_PROGRESS.md
└── requirements.txt
```

## Development progression

1. **RTL/IR foundation:** Start with a small counter or mux design and inspect CIRCT HW/Comb/Seq IR.
2. **SSA dependency extraction:** Identify operation results and operands.
3. **Initial dependence graph:** Create data dependencies and heuristic mux control dependencies.
4. **Temporal model:** Explore cycle offsets for combinational and sequential paths. These assumptions need checking.
5. **Backward slicing:** Traverse a worklist of (signal, cycle) pairs subject to a cycle horizon.
6. **Integrated prototype:** Combine parsing, graph construction and traversal.
7. **Manual validation:** Compare inferred dependencies with an RTL-derived reference.
8. **V4 reduction experiment:** Historical experiment; exact quantitative results are not verified in the current repository snapshot.
9. **V5 experiment:** Working notes report 20 original MLIR operations, 13 retained, and 7 removed (35% of counted operations).
10. **V6 simulation comparison:** Working notes record PASS for original/reduced status outputs under tested sequences. This is not formal equivalence.

Details and evidence status are in [THESIS_PROGRESS.md](THESIS_PROGRESS.md) and [docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md).

## Run the existing graph generator

Generate a DOT graph:

```powershell
python .\src\pdg_from_mlir.py .\examples\simple_mux.mlir .\output\simple_mux.dot
```

With Graphviz installed, render it as PNG:

```powershell
dot -Tpng .\output\simple_mux.dot -o .\output\simple_mux.png
```

The parser uses text/regular-expression heuristics and supports only a limited operation list. It is not a full MLIR parser. Operation-specific operand semantics, clock inputs, scoping and other syntax need more robust treatment.

## Toolchain

The Windows setup in working notes uses local CIRCT binaries such as `circt-verilog.exe` and `circt-opt.exe`. Local paths must be adapted to the actual installation. See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Interpreting the reported V5/V6 results

- The 35% value is a count reduction from 20 to 13 MLIR operations in one reported experiment. It does not imply a 35% area, power, or delay reduction.
- V6 PASS refers to output agreement for the inputs exercised in the recorded testbench, not a formal proof for all possible sequences.
- The current repository snapshot does not yet include the exact V4–V6 scripts and simulation artifacts. Those should be added from the real project files before claiming full reproducibility.
- Novelty claims require a documented literature review and comparison with existing slicing approaches.

## Research hygiene

Record exact inputs, criteria, cycle horizons, commands, tool versions, actual test outputs, and unresolved questions. Avoid committing credentials, unrelated build output, or machine-specific binaries.

## License

No license has been specified yet. Add a license before inviting reuse or redistribution.
