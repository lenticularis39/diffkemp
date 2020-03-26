//===------------------ FFI.h - C interface for SimpLL --------------------===//
//
//       SimpLL - Program simplifier for analysis of semantic difference      //
//
// This file is published under Apache 2.0 license. See LICENSE for details.
// Author: Tomas Glozar, tglozar@gmail.com
//===----------------------------------------------------------------------===//
///
/// \file
/// This file contains declarations of C functions and structure types used for
/// interacting with DiffKemp.
///
//===----------------------------------------------------------------------===//

#ifdef __cplusplus
extern "C" {
#endif

struct config {
    const char *CacheDir;
    const char *Variable;
    int OutputLlvmIR;
    int ControlFlowOnly;
    int PrintAsmDiffs;
    int PrintCallStacks;
    int Verbose;
    int VerboseMacros;
};

void *loadModule(const char *Path);

void freeModule(void *ModRaw);

/// Clones modules to get separate copies of them and runs the simplification
/// and comparison on the copies.
void cloneAndRunSimpLL(void *ModL,
                       void *ModR,
                       const char *ModLOut,
                       const char *ModROut,
                       const char *FunL,
                       const char *FunR,
                       struct config Conf,
                       char *Output);

/// Loads modules from the specified filers and runs the simplification and
/// comparison on the loaded objects, which are discarded after the comparison.
void parseAndRunSimpLL(const char *ModL,
                       const char *ModR,
                       const char *ModLOut,
                       const char *ModROut,
                       const char *FunL,
                       const char *FunR,
                       struct config Conf,
                       char *Output);

void shutdownSimpLL();

#ifdef __cplusplus
}
#endif
