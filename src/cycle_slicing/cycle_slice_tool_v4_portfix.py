import os
import re
import argparse
import subprocess
from dataclasses import dataclass


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MLIR_FILE = "mixed_test_hw.mlir"

CIRCT_OPT = r"F:\Projects\circt\build\bin\circt-opt.exe"


# ============================================================
# DATA STRUCTURE
# ============================================================

@dataclass
class Dependency:
    source: str
    target: str
    dependency_type: str
    offset: int


# ============================================================
# DEPENDENCY TYPE
# ============================================================

def get_dependency_type(operation, operand_index):
    """
    Determine the semantic type of a dependency.
    """

    if operation == "seq.firreg":
        return "STATE"

    if operation == "comb.mux":
        if operand_index == 0:
            return "CONTROL"
        return "DATA"

    if operation.startswith("comb."):
        return "DATA"

    if operation == "seq.to_clock":
        return "CLOCK"

    return None


# ============================================================
# CYCLE OFFSET
# ============================================================

def get_offset(operation):
    """
    Determine the cycle offset.

    comb.*:
        same cycle -> 0

    seq.firreg:
        previous cycle -> -1

    seq.to_clock:
        structural dependency only
    """

    if operation == "seq.firreg":
        return -1

    if operation.startswith("comb."):
        return 0

    if operation == "seq.to_clock":
        return None

    return None


# ============================================================
# BUILD DEPENDENCY GRAPH
# ============================================================

def build_dependencies(mlir_file):
    """
    Parse CIRCT MLIR and construct dependency information.
    """

    with open(mlir_file, "r") as file:
        lines = file.readlines()

    dependencies = {}

    for line in lines:

        line = line.strip()

        if not line:
            continue

        match = re.match(
            r"(%[\w-]+)\s*=\s*([\w.]+)\s+(.*)",
            line
        )

        if not match:
            continue

        result = match.group(1)
        operation = match.group(2)
        operand_text = match.group(3)

        operands = re.findall(
            r"%[\w-]+",
            operand_text
        )

        offset = get_offset(operation)

        if offset is None:
            continue

        dependencies[result] = []

        # ----------------------------------------------------
        # Sequential register
        # ----------------------------------------------------

        if operation == "seq.firreg":

            if operands:

                dependency = Dependency(
                    source=operands[0],
                    target=result,
                    dependency_type="STATE",
                    offset=offset
                )

                dependencies[result].append(
                    dependency
                )

        # ----------------------------------------------------
        # Combinational operation
        # ----------------------------------------------------

        else:

            for index, operand in enumerate(operands):

                dependency_type = get_dependency_type(
                    operation,
                    index
                )

                if dependency_type is None:
                    continue

                dependency = Dependency(
                    source=operand,
                    target=result,
                    dependency_type=dependency_type,
                    offset=offset
                )

                dependencies[result].append(
                    dependency
                )

    return dependencies


# ============================================================
# OUTPUT MAPPING
# ============================================================

def find_output_mapping(mlir_file):
    """
    Map RTL output names to CIRCT SSA values.

    Example:

        out data_copy : i4

    and:

        hw.output %data_copy : i4

    gives:

        data_copy -> %data_copy
    """

    with open(mlir_file, "r") as file:
        text = file.read()

    # --------------------------------------------------------
    # Find module declaration
    # --------------------------------------------------------

    module_match = re.search(
        r"hw\.module\s+@[\w$]+\((.*?)\)\s*\{",
        text,
        re.DOTALL
    )

    if not module_match:

        print(
            "ERROR: hw.module declaration not found."
        )

        return {}

    module_arguments = module_match.group(1)

    # --------------------------------------------------------
    # Find output names
    # --------------------------------------------------------

    output_names = re.findall(
        r"out\s+([\w$]+)\s*:",
        module_arguments
    )

    # --------------------------------------------------------
    # Find hw.output
    # --------------------------------------------------------

    output_match = re.search(
        r"hw\.output\s+(.*?)\s*:",
        text
    )

    if not output_match:

        print(
            "ERROR: hw.output operation not found."
        )

        return {}

    output_text = output_match.group(1)

    output_values = re.findall(
        r"%[\w-]+",
        output_text
    )

    # --------------------------------------------------------
    # Build mapping
    # --------------------------------------------------------

    mapping = {}

    count = min(
        len(output_names),
        len(output_values)
    )

    for index in range(count):

        output_name = output_names[index]
        ssa_value = output_values[index]

        mapping[output_name] = ssa_value

    return mapping


# ============================================================
# READ MLIR OPERATIONS
# ============================================================

def read_mlir_operations(mlir_file):
    """
    Read SSA-producing operations from MLIR.
    """

    with open(mlir_file, "r") as file:
        lines = file.readlines()

    operations = []

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        # Module declaration
        if stripped.startswith("hw.module"):
            continue

        # Closing braces
        if stripped in ["}", "};"]:
            continue

        # hw.output handled separately
        if stripped.startswith("hw.output"):
            continue

        # SSA-producing operation
        if re.match(
            r"%[\w-]+\s*=",
            stripped
        ):

            operations.append(
                stripped
            )

    return operations


# ============================================================
# GET SSA RESULT
# ============================================================

def get_result_ssa(operation):
    """
    Extract SSA result.

    Example:

        %10 = comb.mux ...

    returns:

        %10
    """

    match = re.match(
        r"(%[\w-]+)\s*=",
        operation
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# BACKWARD CYCLE-AWARE SLICE
# ============================================================

def backward_slice(
    signal,
    cycle,
    min_cycle,
    dependencies
):
    """
    Perform backward cycle-aware slicing.

    Combinational dependency:

        target @ t
            depends on
        source @ t

    Sequential dependency:

        register @ t
            depends on
        source @ t-1
    """

    worklist = [
        (signal, cycle)
    ]

    visited = set()

    while worklist:

        current_signal, current_cycle = worklist.pop()

        if current_cycle < min_cycle:
            continue

        node = (
            current_signal,
            current_cycle
        )

        if node in visited:
            continue

        visited.add(node)

        print(
            f"Visiting {current_signal} "
            f"at cycle {current_cycle}"
        )

        for dependency in dependencies.get(
            current_signal,
            []
        ):

            source = dependency.source
            offset = dependency.offset

            source_cycle = (
                current_cycle + offset
            )

            if source_cycle >= min_cycle:

                worklist.append(
                    (
                        source,
                        source_cycle
                    )
                )

    return visited


# ============================================================
# STRUCTURAL DEPENDENCIES
# ============================================================

def find_structural_dependencies(
    operations,
    semantic_keep
):
    """
    Find structural dependencies required by
    retained sequential operations.

    Example:

        %count = seq.firreg %6 clock %4

    requires:

        %4 = seq.to_clock %clk
    """

    structural_keep = set()

    for operation in operations:

        result = get_result_ssa(
            operation
        )

        if result is None:
            continue

        if result not in semantic_keep:
            continue

        if "seq.firreg" not in operation:
            continue

        operands = re.findall(
            r"%[\w-]+",
            operation
        )

        # Example:
        #
        # %count
        # %6
        # %4

        if len(operands) < 3:
            continue

        clock_ssa = operands[2]

        structural_keep.add(
            clock_ssa
        )

    return structural_keep


# ============================================================
# GENERATE REDUCED MLIR
# ============================================================

def generate_reduced_mlir(
    mlir_file,
    reduced_file,
    operations,
    semantic_keep,
    structural_keep,
    criterion_ssa,
    criterion_output
):
    """
    Generate reduced CIRCT MLIR.

    The reduced module contains:

    - all original input ports
    - ONLY the selected criterion output
    - retained semantic operations
    - required structural operations
    - selected criterion as hw.output
    """

    with open(
        mlir_file,
        "r"
    ) as file:

        text = file.read()

    # ========================================================
    # FIND MODULE
    # ========================================================

    module_match = re.search(
        r"hw\.module\s+@([\w$]+)\((.*?)\)\s*\{",
        text,
        re.DOTALL
    )

    if not module_match:

        raise RuntimeError(
            "Could not find hw.module declaration."
        )

    module_name = module_match.group(1)
    module_ports = module_match.group(2)

    # ========================================================
    # FIND ORIGINAL OUTPUTS
    # ========================================================

    output_pattern = re.compile(
        r"out\s+([\w$]+)\s*:\s*([^,)\n]+)"
    )

    output_matches = output_pattern.findall(
        module_ports
    )

    output_types = {}

    for name, data_type in output_matches:

        output_types[name] = (
            data_type.strip()
        )

    # ========================================================
    # CHECK CRITERION OUTPUT
    # ========================================================

    if criterion_output not in output_types:

        raise RuntimeError(
            f"Criterion output "
            f"'{criterion_output}' "
            f"not found in module interface."
        )

    criterion_type = output_types[
        criterion_output
    ]

    # ========================================================
    # REMOVE ALL ORIGINAL OUTPUT PORTS
    # ========================================================

    input_ports = re.sub(
        r",?\s*out\s+[\w$]+\s*:\s*[^,)\n]+",
        "",
        module_ports
    )

    input_ports = input_ports.strip()

    # ========================================================
    # ADD ONLY SELECTED OUTPUT
    # ========================================================

    if input_ports:

        reduced_ports = (
            input_ports
            + ", out "
            + criterion_output
            + " : "
            + criterion_type
        )

    else:

        reduced_ports = (
            "out "
            + criterion_output
            + " : "
            + criterion_type
        )

    # NOTE: boundary_ports (computed below, after retained
    # operations are known) are spliced in just before the
    # final MLIR text is assembled -- see BOUNDARY_PORTS_MARKER.

    # ========================================================
    # RETAIN OPERATIONS
    # ========================================================

    retained_operations = []

    for operation in operations:

        result = get_result_ssa(
            operation
        )

        if result is None:
            continue

        if (
            result in semantic_keep
            or result in structural_keep
        ):

            retained_operations.append(
                operation
            )

    # ========================================================
    # FIND BOUNDARY OPERANDS
    # ========================================================
    #
    # A kept operation (usually a seq.firreg we keep for
    # STRUCTURAL reasons, e.g. to preserve register identity)
    # may reference an SSA value whose *producing* operation
    # was cut because it fell outside the cycle-bounded slice.
    #
    # That reference must not be left dangling: we promote it
    # to a new module input port of the same type, with the
    # same SSA name it already had. Because CIRCT/MLIR block
    # arguments are referenced by name, no rewriting of the
    # retained operation text is needed -- only the port list
    # changes.

    retained_results = set()

    for operation in retained_operations:
        result = get_result_ssa(operation)
        if result is not None:
            retained_results.add(result)

    original_input_names = set(
        re.findall(r"in\s+(%[\w-]+)", module_ports)
    )

    def infer_type(ssa_name, full_text):
        """
        Best-effort lookup of the MLIR type of ssa_name by
        scanning the original (unreduced) module text for its
        defining line. Handles both ': type' results and
        '-> type' results (e.g. comb.extract).
        """
        pattern = re.compile(
            r"^\s*" + re.escape(ssa_name) +
            r"\s*=.*$",
            re.MULTILINE
        )
        match = pattern.search(full_text)
        if not match:
            return "i1"  # safe-ish fallback; should not happen
        line = match.group(0)
        arrow = re.search(r"->\s*([^\s,)]+)", line)
        if arrow:
            return arrow.group(1).rstrip(")")
        colon_matches = re.findall(r":\s*([^\s,)]+)", line)
        if colon_matches:
            return colon_matches[-1].rstrip(")")
        return "i1"

    boundary_ports = []
    seen_boundary = set()

    for operation in retained_operations:
        result = get_result_ssa(operation)
        rhs = operation.split("=", 1)[1] if "=" in operation else operation
        operands = re.findall(r"%[\w-]+", rhs)
        for operand in operands:
            if operand == result:
                continue
            if operand in retained_results:
                continue
            if operand in original_input_names:
                continue
            if operand in seen_boundary:
                continue
            seen_boundary.add(operand)
            operand_type = infer_type(operand, text)
            boundary_ports.append(
                f"in {operand} : {operand_type}"
            )

    # ========================================================
    # BUILD MODULE BODY
    # ========================================================

    new_body_lines = []

    for operation in retained_operations:

        new_body_lines.append(
            "    " + operation
        )

    # ========================================================
    # ADD SELECTED OUTPUT
    # ========================================================

    new_body_lines.append(
        f"    hw.output "
        f"{criterion_ssa} : "
        f"{criterion_type}"
    )

    # ========================================================
    # CREATE REDUCED MLIR TEXT
    # ========================================================

    # BOUNDARY_PORTS_MARKER
    if boundary_ports:
        final_ports = (
            reduced_ports + ", " + ", ".join(boundary_ports)
        )
    else:
        final_ports = reduced_ports

    reduced_text = (
        f"hw.module @{module_name}("
        f"{final_ports}) {{\n"
        + "\n".join(new_body_lines)
        + "\n}\n"
    )

    # ========================================================
    # WRITE FILE
    # ========================================================

    with open(
        reduced_file,
        "w"
    ) as file:

        file.write(
            reduced_text
        )


# ============================================================
# CIRCT MLIR VALIDATION
# ============================================================

def validate_with_circt_opt(
    reduced_mlir_file,
    experiment_dir
):
    """
    Validate the generated reduced MLIR using circt-opt.

    Returns:

        True  -> validation successful
        False -> validation failed
    """

    print()
    print(
        "=============================================="
    )
    print(
        " CIRCT MLIR VALIDATION"
    )
    print(
        "=============================================="
    )

    # --------------------------------------------------------
    # Check circt-opt
    # --------------------------------------------------------

    if not os.path.exists(CIRCT_OPT):

        print(
            "ERROR: circt-opt not found:"
        )

        print(
            f"    {CIRCT_OPT}"
        )

        return False

    # --------------------------------------------------------
    # Validation report
    # --------------------------------------------------------

    validation_file = os.path.join(
        experiment_dir,
        "validation.txt"
    )

    # --------------------------------------------------------
    # Run circt-opt
    # --------------------------------------------------------

    try:

        result = subprocess.run(
            [
                CIRCT_OPT,
                reduced_mlir_file
            ],
            capture_output=True,
            text=True
        )

    except Exception as error:

        print(
            "ERROR: Could not execute circt-opt."
        )

        print(
            f"    {error}"
        )

        return False

    # --------------------------------------------------------
    # Save validation report
    # --------------------------------------------------------

    with open(
        validation_file,
        "w"
    ) as file:

        file.write(
            "CIRCT MLIR VALIDATION\n"
        )

        file.write(
            "=====================\n\n"
        )

        file.write(
            "Input file:\n"
        )

        file.write(
            f"{reduced_mlir_file}\n\n"
        )

        file.write(
            "circt-opt:\n"
        )

        file.write(
            f"{CIRCT_OPT}\n\n"
        )

        file.write(
            "Return code: "
        )

        file.write(
            f"{result.returncode}\n\n"
        )

        file.write(
            "STDOUT\n"
        )

        file.write(
            "------\n"
        )

        file.write(
            result.stdout
        )

        file.write(
            "\n\n"
        )

        file.write(
            "STDERR\n"
        )

        file.write(
            "------\n"
        )

        file.write(
            result.stderr
        )

    # --------------------------------------------------------
    # PASS
    # --------------------------------------------------------

    if result.returncode == 0:

        print()
        print(
            "CIRCT VALIDATION: PASS"
        )

        print(
            "Reduced MLIR is valid."
        )

        print()
        print(
            "Validation report:"
        )

        print(
            f"    {validation_file}"
        )

        return True

    # --------------------------------------------------------
    # FAIL
    # --------------------------------------------------------

    print()
    print(
        "CIRCT VALIDATION: FAIL"
    )

    print(
        "circt-opt reported an error."
    )

    if result.stderr:

        print()
        print(
            "Error:"
        )

        print(
            result.stderr
        )

    print()
    print(
        "Validation report:"
    )

    print(
        f"    {validation_file}"
    )

    return False


# ============================================================
# CIRCT SYSTEMVERILOG GENERATION
# ============================================================

def generate_systemverilog(reduced_mlir_file, output_sv_file, experiment_dir):
    """
    Generate SystemVerilog from reduced MLIR using CIRCT.

    CIRCT emits generated SystemVerilog followed by textual MLIR.
    We keep only the generated SystemVerilog section.
    """

    print("\n==============================================")
    print(" CIRCT SYSTEMVERILOG GENERATION")
    print("==============================================")

    try:
        result = subprocess.run(
            [
                CIRCT_OPT,
                reduced_mlir_file,
                "--lower-seq-to-sv",
                "--lower-hw-to-sv",
                "--export-verilog",
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            print("CIRCT SV generation: FAILED")
            print(result.stderr)

            with open(
                os.path.join(experiment_dir, "sv_export_error.txt"),
                "w",
                encoding="utf-8"
            ) as f:
                f.write(result.stderr)

            return False

        output = result.stdout

        # ---------------------------------------------------------
        # CIRCT output structure:
        #
        #   // Generated by CIRCT ...
        #   ...
        #   module mixed_test(...)
        #   ...
        #   endmodule
        #
        #   module {
        #       ... textual MLIR ...
        #   }
        #
        # We only want the first section.
        # ---------------------------------------------------------

        match = re.search(
            r"(?m)^endmodule\s*$",
            output
        )

        if match is None:
            print("CIRCT SV generation: FAILED")
            print("Could not find generated SystemVerilog endmodule.")

            with open(
                os.path.join(experiment_dir, "sv_export_error.txt"),
                "w",
                encoding="utf-8"
            ) as f:
                f.write(output)

            return False

        # Keep everything from CIRCT's generated header through
        # the first SystemVerilog endmodule.
        clean_sv = output[:match.end()] + "\n"

        # Remove CIRCT's optional register-randomization block.
        #
        # This block starts with:
        #     `ifdef ENABLE_INITIAL_REG_
        #
        # and ends with:
        #     `endif // ENABLE_INITIAL_REG_
        #
        # It is not part of the functional RTL behavior that we
        # want to compare in the slicing experiment.

        clean_sv = re.sub(
            r"\s*`ifdef ENABLE_INITIAL_REG_.*?`endif // ENABLE_INITIAL_REG_",
            "",
            clean_sv,
            flags=re.DOTALL
        )

        with open(
            output_sv_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(clean_sv)

        print("CIRCT SV generation: PASS")
        print()
        print("Reduced SystemVerilog:")
        print(f"    {output_sv_file}")

        return True

    except Exception as e:

        print("CIRCT SV generation: FAILED")
        print(str(e))

        with open(
            os.path.join(experiment_dir, "sv_export_error.txt"),
            "w",
            encoding="utf-8"
        ) as f:
            f.write(str(e))

        return False

    # --------------------------------------------------------
    # Check result
    # --------------------------------------------------------

    if result.returncode != 0:

        with open(
            error_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "CIRCT SYSTEMVERILOG GENERATION ERROR\n"
            )

            file.write(
                "====================================\n\n"
            )

            file.write(
                "Input file:\n"
            )

            file.write(
                f"{reduced_mlir_file}\n\n"
            )

            file.write(
                "Command:\n"
            )

            file.write(
                f"{CIRCT_OPT} "
                f"{reduced_mlir_file} "
                f"--lower-seq-to-sv "
                f"--lower-hw-to-sv "
                f"--export-verilog\n\n"
            )

            file.write(
                "Return code:\n"
            )

            file.write(
                f"{result.returncode}\n\n"
            )

            file.write(
                "STDOUT\n"
            )

            file.write(
                "------\n"
            )

            file.write(
                result.stdout
            )

            file.write(
                "\n\n"
            )

            file.write(
                "STDERR\n"
            )

            file.write(
                "------\n"
            )

            file.write(
                result.stderr
            )

        print()
        print(
            "CIRCT SV generation: FAIL"
        )

        print()
        print(
            "Error report:"
        )

        print(
            f"    {error_file}"
        )

        return False

    # --------------------------------------------------------
    # Save generated SystemVerilog
    # --------------------------------------------------------

    with open(
        output_sv_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            result.stdout
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print()
    print(
        "CIRCT SV generation: PASS"
    )

    print()
    print(
        "Reduced SystemVerilog:"
    )

    print(
        f"    {output_sv_file}"
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # ARGUMENT PARSER
    # ========================================================

    parser = argparse.ArgumentParser(
        description=(
            "Cycle-aware RTL slicing tool "
            "for CIRCT MLIR"
        )
    )

    parser.add_argument(
        "--mlir",
        default=DEFAULT_MLIR_FILE,
        help=(
            "Input CIRCT MLIR file "
            "(default: mixed_test_hw.mlir)"
        )
    )

    parser.add_argument(
        "--output",
        required=True,
        help=(
            "RTL output used as slicing criterion"
        )
    )

    parser.add_argument(
        "--cycle",
        required=True,
        type=int,
        help=(
            "Cycle of the slicing criterion"
        )
    )

    parser.add_argument(
        "--min-cycle",
        type=int,
        default=0,
        help=(
            "Minimum cycle considered "
            "(default: 0)"
        )
    )

    parser.add_argument(
        "--reduced",
        default=None,
        help=(
            "Optional custom output path "
            "for reduced MLIR"
        )
    )

    args = parser.parse_args()

    # ========================================================
    # ARGUMENT VALUES
    # ========================================================

    mlir_file = args.mlir
    criterion_output = args.output
    criterion_cycle = args.cycle
    min_cycle = args.min_cycle

    # ========================================================
    # HEADER
    # ========================================================

    print(
        "=============================================="
    )

    print(
        " CYCLE-AWARE RTL SLICING TOOL"
    )

    print(
        "=============================================="
    )

    print()

    print(
        f"Input MLIR       : {mlir_file}"
    )

    print(
        f"Criterion output : {criterion_output}"
    )

    print(
        f"Criterion cycle  : {criterion_cycle}"
    )

    print(
        f"Minimum cycle    : {min_cycle}"
    )

    print()

    # ========================================================
    # CHECK INPUT MLIR
    # ========================================================

    if not os.path.exists(
        mlir_file
    ):

        print(
            f"ERROR: MLIR file not found: "
            f"{mlir_file}"
        )

        return

    # ========================================================
    # CREATE EXPERIMENT DIRECTORY
    # ========================================================

    experiment_dir = os.path.join(
        "experiments",
        f"{criterion_output}_cycle{criterion_cycle}"
    )

    os.makedirs(
        experiment_dir,
        exist_ok=True
    )

    # ========================================================
    # REDUCED MLIR OUTPUT
    # ========================================================

    if args.reduced:

        reduced_mlir_file = (
            args.reduced
        )

    else:

        reduced_mlir_file = os.path.join(
            experiment_dir,
            "reduced.mlir"
        )

    # ========================================================
    # READ MLIR OPERATIONS
    # ========================================================

    operations = read_mlir_operations(
        mlir_file
    )

    # ========================================================
    # OUTPUT MAPPING
    # ========================================================

    output_mapping = find_output_mapping(
        mlir_file
    )

    if criterion_output not in output_mapping:

        print(
            "ERROR: Requested output "
            f"'{criterion_output}' "
            "was not found."
        )

        print()

        print(
            "Available outputs:"
        )

        for name in output_mapping:

            print(
                f"    {name}"
            )

        return

    criterion_ssa = output_mapping[
        criterion_output
    ]

    # ========================================================
    # PRINT CRITERION
    # ========================================================

    print(
        "RTL slicing criterion:"
    )

    print(
        f"    <{criterion_output},"
        f"{criterion_cycle}>"
    )

    print()

    print(
        "CIRCT SSA criterion:"
    )

    print(
        f"    <{criterion_ssa},"
        f"{criterion_cycle}>"
    )

    print()

    # ========================================================
    # BUILD DEPENDENCIES
    # ========================================================

    dependencies = build_dependencies(
        mlir_file
    )

    # ========================================================
    # BACKWARD SLICE
    # ========================================================

    visited = backward_slice(
        criterion_ssa,
        criterion_cycle,
        min_cycle,
        dependencies
    )

    # ========================================================
    # TEMPORAL SEMANTIC SLICE
    # ========================================================

    temporal_slice = set()

    for signal, cycle in visited:

        temporal_slice.add(
            (signal, cycle)
        )

    print()

    print(
        "===== TEMPORAL SEMANTIC SLICE ====="
    )

    for signal, cycle in sorted(
        temporal_slice,
        key=lambda item: (item[1], item[0])
    ):

        print(
            f"{signal} @ cycle {cycle}"
        )


    # ========================================================
    # TEMPORAL OPERATION MAP
    # ========================================================

    temporal_operation_map = {}

    for signal, cycle in temporal_slice:

        if signal not in temporal_operation_map:
            temporal_operation_map[signal] = set()

        temporal_operation_map[signal].add(
            cycle
        )

    print()

    print(
        "===== TEMPORAL OPERATION MAP ====="
    )

    for signal in sorted(
        temporal_operation_map
    ):

        cycles = sorted(
            temporal_operation_map[signal]
        )

        print(
            f"{signal} -> cycles {cycles}"
        )


    # ========================================================
    # SEMANTIC KEEP
    # ========================================================

    semantic_keep = set(
        temporal_operation_map.keys()
    )

    print()

    print(
        "===== SEMANTIC KEEP ====="
    )

    for signal in sorted(
        semantic_keep
    ):

        print(
            signal
        )

    # ========================================================
    # STRUCTURAL KEEP
    # ========================================================

    structural_keep = (
        find_structural_dependencies(
            operations,
            semantic_keep
        )
    )

    print()

    print(
        "===== STRUCTURAL KEEP ====="
    )

    for signal in sorted(
        structural_keep
    ):

        print(signal)

    # ========================================================
    # FINAL RETAINED OPERATIONS
    # ========================================================

    final_keep_operations = []

    for operation in operations:

        result = get_result_ssa(
            operation
        )

        if result is None:
            continue

        if (
            result in semantic_keep
            or result in structural_keep
        ):

            final_keep_operations.append(
                operation
            )

    # ========================================================
    # REMOVED OPERATIONS
    # ========================================================

    remove_operations = []

    for operation in operations:

        result = get_result_ssa(
            operation
        )

        if result is None:
            continue

        if (
            result not in semantic_keep
            and result not in structural_keep
        ):

            remove_operations.append(
                operation
            )

    # ========================================================
    # PRINT RETAINED OPERATIONS
    # ========================================================

    print()

    print(
        "===== FINAL KEEP OPERATIONS ====="
    )

    for operation in final_keep_operations:

        print(operation)

    # ========================================================
    # PRINT REMOVED OPERATIONS
    # ========================================================

    print()

    print(
        "===== REMOVE OPERATIONS ====="
    )

    for operation in remove_operations:

        print(operation)

    # ========================================================
    # STATISTICS
    # ========================================================

    # Total static MLIR operations in the input
    original_count = len(
        operations
    )

    # Number of temporal (SSA value, cycle) nodes
    temporal_node_count = len(
        temporal_slice
    )

    # Number of unique SSA values participating
    unique_value_count = len(
        semantic_keep
    )

    # Number of unique MLIR operations that are
    # semantically relevant
    relevant_operation_count = 0

    for operation in operations:

        result = get_result_ssa(
            operation
        )

        if result is None:
            continue

        if result in semantic_keep:

            relevant_operation_count += 1

    # Structural dependencies such as the clock
    structural_count = len(
        structural_keep
    )

    # Final operations actually retained
    final_count = len(
        final_keep_operations
    )

    # Operations removed from the static RTL
    removable_count = (
        original_count
        - final_count
    )

    reduction = 0.0

    if original_count > 0:

        reduction = (
            removable_count
            / original_count
        ) * 100.0

    # ========================================================
    # GENERATE REDUCED MLIR
    # ========================================================

    generate_reduced_mlir(
        mlir_file,
        reduced_mlir_file,
        operations,
        semantic_keep,
        structural_keep,
        criterion_ssa,
        criterion_output
    )

    # ========================================================
    # CIRCT VALIDATION
    # ========================================================

    validation_passed = (
        validate_with_circt_opt(
            reduced_mlir_file,
            experiment_dir
        )
    )

    # ========================================================
    # CIRCT SYSTEMVERILOG GENERATION
    # ========================================================

    sv_file = os.path.join(
        experiment_dir,
        "reduced.sv"
    )

    sv_generation_passed = False

    if validation_passed:

        sv_generation_passed = (
            generate_systemverilog(
                reduced_mlir_file,
                sv_file,
                experiment_dir
            )
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()

    print(
        "=============================================="
    )

    print(
        " CYCLE SLICING RESULT"
    )

    print(
        "=============================================="
    )

    print()

    print(
        f"Original MLIR operations        : "
        f"{original_count}"
    )

    print(
        f"Temporal slice nodes             : "
        f"{temporal_node_count}"
    )

    print(
        f"Unique relevant SSA values       : "
        f"{unique_value_count}"
    )

    print(
        f"Relevant MLIR operations         : "
        f"{relevant_operation_count}"
    )

    print(
        f"Structural dependencies          : "
        f"{structural_count}"
    )

    print(
        f"Final retained operations        : "
        f"{final_count}"
    )

    print(
        f"Final removable operations       : "
        f"{removable_count}"
    )

    print(
        f"Potential reduction              : "
        f"{reduction:.2f}%"
    )

    print()

    print(
        "Reduced MLIR file:"
    )

    print(
        f"    {reduced_mlir_file}"
    )

    print()

    print(
        "Experiment directory:"
    )

    print(
        f"    {experiment_dir}"
    )

    print()

    if validation_passed:

        print(
            "CIRCT validation status     : PASS"
        )

    else:

        print(
            "CIRCT validation status     : FAIL"
        )

    if sv_generation_passed:

        print(
            "SystemVerilog generation    : PASS"
        )

        print()

        print(
            "Reduced SystemVerilog:"
        )

        print(
            f"    {sv_file}"
        )

    else:

        print(
            "SystemVerilog generation    : FAIL"
        )

    print()

    print(
        "Cycle slicing completed."
    )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()


