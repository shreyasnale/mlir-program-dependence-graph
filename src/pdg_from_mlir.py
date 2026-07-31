import re
import sys

if len(sys.argv) != 3:
    print("Usage: python pdg_from_mlir.py input.mlir output.dot")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

ssa_re = re.compile(r"%[A-Za-z0-9_.$-]+")

ops = [
    "comb.mux",
    "comb.add",
    "comb.sub",
    "comb.mul",
    "comb.and",
    "comb.or",
    "comb.xor",
    "comb.not",
    "comb.icmp",
    "seq.firreg",
    "seq.to_clock",
    "hw.constant",
    "hw.output"
]

def find_op(line):
    for op in ops:
        if op in line:
            return op
    return None

def escape_dot(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')

nodes = []
edges = []

producer = {}
inputs = {}
node_id = 0

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line_no, raw in enumerate(lines, start=1):
    line = raw.strip()

    if not line or line.startswith("//"):
        continue

    op = find_op(line)
    if op is None:
        continue

    current_node = f"n{node_id}"
    node_id += 1

    results = []

    if "=" in line:
        left, right = line.split("=", 1)
        results = ssa_re.findall(left)
        operand_part = right
    else:
        operand_part = line

    operands = ssa_re.findall(operand_part)

    label = op
    if results:
        label += "\\n" + ", ".join(results)

    nodes.append((current_node, label, op))

    for r in results:
        producer[r] = current_node

    control_operands = set()

    if op == "comb.mux" and len(operands) >= 3:
        control_operands.add(operands[0])

    for operand in operands:
        if operand in producer:
            src = producer[operand]
        else:
            if operand not in inputs:
                input_node = f"in{len(inputs)}"
                inputs[operand] = input_node
                nodes.append((input_node, operand, "input"))
            src = inputs[operand]

        if operand in control_operands:
            edges.append((src, current_node, "control"))
        else:
            edges.append((src, current_node, "data"))

with open(output_file, "w", encoding="utf-8") as f:
    f.write("digraph VerilogPDG {\n")
    f.write("  rankdir=LR;\n")
    f.write("  graph [fontname=\"Consolas\"];\n")
    f.write("  node [shape=ellipse, fontname=\"Consolas\", fontsize=11];\n")
    f.write("  edge [fontname=\"Consolas\", fontsize=10];\n\n")

    f.write("  legend1 [label=\"Thick red dashed = control dependence\", shape=box];\n")
    f.write("  legend2 [label=\"Thin blue solid = data dependence\", shape=box];\n\n")

    for nid, label, op in nodes:
        label = escape_dot(label)

        if op == "input":
            f.write(f'  {nid} [label="{label}", shape=oval];\n')
        elif op == "comb.mux":
            f.write(f'  {nid} [label="{label}", shape=ellipse, style=filled, fillcolor="#fff2cc"];\n')
        elif op == "seq.firreg":
            f.write(f'  {nid} [label="{label}", shape=ellipse, style=filled, fillcolor="#d9eaf7"];\n')
        elif op == "hw.constant":
            f.write(f'  {nid} [label="{label}", shape=ellipse, style=filled, fillcolor="#f7c6c7"];\n')
        elif op == "hw.output":
            f.write(f'  {nid} [label="{label}", shape=ellipse, style=filled, fillcolor="#e6ddff"];\n')
        else:
            f.write(f'  {nid} [label="{label}", shape=ellipse];\n')

    f.write("\n")

    for src, dst, kind in edges:
        if kind == "control":
            f.write(f'  {src} -> {dst} [label="control", color="red", style="dashed", penwidth=3];\n')
        else:
            f.write(f'  {src} -> {dst} [label="data", color="blue", penwidth=1];\n')

    f.write("}\n")

print("Generated:", output_file)