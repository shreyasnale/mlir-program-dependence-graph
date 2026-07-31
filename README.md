\# MLIR Program Dependence Graph Generator



A Python-based tool for generating a simplified Program Dependence Graph

from CIRCT/MLIR hardware descriptions.



The project supports the analysis of data dependencies and control

dependencies in hardware-oriented intermediate representations.



\## Project Motivation



This work is related to a research project on transforming SystemVerilog

descriptions into LLVM/CIRCT MLIR and developing a program slicer for

digital hardware designs.



\## Features



\- Parses selected CIRCT/MLIR operations

\- Detects SSA values and their producers

\- Generates data-dependence edges

\- Identifies control relationships around operations such as `comb.mux`

\- Produces Graphviz DOT output

\- Generates visual PNG graphs



\## Technologies



\- Python

\- LLVM

\- MLIR

\- CIRCT

\- SystemVerilog

\- Graphviz



\## Repository Structure



```text

src/       Python source code

examples/  Sample MLIR input files

output/    Generated DOT and PNG files

docs/      Project documentation

