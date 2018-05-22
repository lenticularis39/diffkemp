from __future__ import absolute_import

from argparse import ArgumentParser
from diffkemp.llvm_ir.build_llvm import LlvmKernelModule
from diffkemp.semdiff.module_diff import modules_diff, Statistics
from diffkemp.semdiff.function_diff import Result
import sys


def __make_argument_parser():
    """ Parsing arguments. """
    ap = ArgumentParser()
    ap.add_argument("module_dir")
    ap.add_argument("module_name")
    ap.add_argument("parameter")
    ap.add_argument("src_version")
    ap.add_argument("dest_version")
    ap.add_argument("-d", "--debug", help="compile module with -g",
                    action="store_true")
    ap.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
    return ap


def run_from_cli():
    """ Main method to run the tool. """
    ap = __make_argument_parser()
    args = ap.parse_args()

    try:
        # Build old module
        first_mod = LlvmKernelModule(args.src_version, args.module_dir,
                                     args.module_name, args.parameter,
                                     args.debug, args.verbose)
        first_mod.build()

        # Build new module
        second_mod = LlvmKernelModule(args.dest_version, args.module_dir,
                                      args.module_name, args.parameter,
                                      args.debug, args.verbose)
        second_mod.build()

        # Compare modules
        stat = modules_diff(first_mod.llvm, second_mod.llvm, args.parameter,
                            args.verbose)
        print ""
        stat.report()

        result = stat.overall_result()
    except Exception as e:
        result = Result.ERROR
        sys.stderr.write("Error: %s\n" % str(e))

    if result == Result.EQUAL:
        print("Semantics of the module parameter is same")
    elif result == Result.NOT_EQUAL:
        print("Semantics of the module parameter has changed")
    else:
        print("Unable to determine changes in semantics of the parameter")
    return result

