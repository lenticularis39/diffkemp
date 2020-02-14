"""
Simplifying LLVM modules with the SimpLL tool.
"""
from diffkemp.semdiff.caching import ComparisonGraph
from diffkemp.llvm_ir.kernel_module import LlvmKernelModule
import os
from subprocess import check_call, check_output, CalledProcessError
import yaml


class SimpLLException(Exception):
    pass


def add_suffix(file, suffix):
    """Add suffix to the file name."""
    name, ext = os.path.splitext(file)
    return "{}-{}{}".format(name, suffix, ext)


def run_simpll(first, second, fun_first, fun_second, var, suffix=None,
               cache_dir=None, control_flow_only=False, print_asm_diffs=False,
               verbose=False):
    """
    Simplify modules to ease their semantic difference. Uses the SimpLL tool.
    :return A tuple containing the two LLVM IR files generated by SimpLL
            followed by the result of the comparison in the form of a graph and
            a list of missing function definitions.
    """
    stderr = None
    if not verbose:
        stderr = open(os.devnull, "w")

    first_out_name = add_suffix(first, suffix) if suffix else first
    second_out_name = add_suffix(second, suffix) if suffix else second

    try:
        # Determine the SimpLL binary to use.
        # The manually built one has priority over the installed one.
        if os.path.isfile("build/diffkemp/simpll/diffkemp-simpll"):
            simpll_bin = "build/diffkemp/simpll/diffkemp-simpll"
        else:
            simpll_bin = "diffkemp-simpll"
        # SimpLL command
        simpll_command = list([simpll_bin, first, second,
                               "--print-callstacks"])
        # Main (analysed) functions
        simpll_command.append("--fun")
        if fun_first != fun_second:
            simpll_command.append("{},{}".format(fun_first, fun_second))
        else:
            simpll_command.append(fun_first)
        # Analysed variable
        if var:
            simpll_command.extend(["--var", var])
        # Suffix for output files
        if suffix:
            simpll_command.extend(["--suffix", suffix])
        # Cache directory with equal function pairs
        if cache_dir:
            simpll_command.extend(["--cache-dir", cache_dir])

        if control_flow_only:
            simpll_command.append("--control-flow")

        if print_asm_diffs:
            simpll_command.append("--print-asm-diffs")

        if verbose:
            simpll_command.append("--verbose")
            print(" ".join(simpll_command))

        simpll_out = check_output(simpll_command)
        check_call(["opt", "-S", "-deadargelim", "-o", first_out_name,
                    first_out_name],
                   stderr=stderr)
        check_call(["opt", "-S", "-deadargelim", "-o", second_out_name,
                    second_out_name],
                   stderr=stderr)

        first_out = LlvmKernelModule(first_out_name)
        second_out = LlvmKernelModule(second_out_name)

        missing_defs = None
        try:
            graph = ComparisonGraph()
            simpll_result = yaml.safe_load(simpll_out)
            if simpll_result is not None:
                if "function-results" in simpll_result:
                    for fun_result in simpll_result["function-results"]:
                        # Create the vertex from the result and insert it into
                        # the graph.
                        vertex = ComparisonGraph.Vertex.from_yaml(fun_result,
                                                                  graph)
                        # Prefer pointed name to ensure that a difference
                        # contaning the variant function as either the left or
                        # the right side has its name in the key.
                        # This is useful because one can tell this is a weak
                        # vertex from its name.
                        if "." in vertex.names[ComparisonGraph.Side.LEFT]:
                            graph[vertex.names[ComparisonGraph.Side.LEFT]] = \
                                vertex
                        else:
                            graph[vertex.names[ComparisonGraph.Side.RIGHT]] = \
                                vertex
                graph.normalize()
                graph.populate_predecessor_lists()
                graph.mark_uncachable_from_assumed_equal()
                missing_defs = simpll_result["missing-defs"] \
                    if "missing-defs" in simpll_result else None
        except yaml.YAMLError:
            pass

        return first_out, second_out, graph, missing_defs
    except CalledProcessError:
        raise SimpLLException("Simplifying files failed")
