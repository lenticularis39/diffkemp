//===------------------- Output.h - Reporting results ---------------------===//
//
//       SimpLL - Program simplifier for analysis of semantic difference      //
//
// This file is published under Apache 2.0 license. See LICENSE for details.
// Author: Viktor Malik, vmalik@redhat.com
//===----------------------------------------------------------------------===//
///
/// \file
/// This file contains classes for reporting results of the simplification.
/// Result is printed as a YAML to stdout.
/// Uses LLVM's YAML library.
///
//===----------------------------------------------------------------------===//

#include "Output.h"
#include <llvm/Support/YAMLTraits.h>

using namespace llvm::yaml;

// CallInfo to YAML
namespace llvm::yaml {
template<>
struct MappingTraits<CallInfo> {
    static void mapping(IO &io, CallInfo &callinfo) {
        io.mapRequired("function", callinfo.fun);
        io.mapRequired("file", callinfo.file);
        io.mapRequired("line", callinfo.line);
    }
};
}

// CallStack (vector of CallInfo) to YAML
LLVM_YAML_IS_SEQUENCE_VECTOR(CallInfo);

// Info about a single function in a non-equal function pair
struct FunctionInfo {
    std::string name;
    std::string file;
    CallStack callstack;

    // Default constructor is needed for YAML serialisation so that the struct
    // can be used as an optional YAML field.
    FunctionInfo() {}
    FunctionInfo(const std::string &name,
                 const std::string &file,
                 const CallStack &callstack)
            : name(name), file(file), callstack(callstack) {}
};

// FunctionInfo to YAML
namespace llvm::yaml {
template<>
struct MappingTraits<FunctionInfo> {
    static void mapping(IO &io, FunctionInfo &info) {
        io.mapRequired("function", info.name);
        io.mapOptional("file", info.file);
        io.mapOptional("callstack", info.callstack);
    }
};
}

// Pair of different functions that will be reported
typedef std::pair<FunctionInfo, FunctionInfo> DiffFunPair;

// DiffFunPair to YAML
namespace llvm::yaml {
template<>
struct MappingTraits<DiffFunPair> {
    static void mapping(IO &io, DiffFunPair &funs) {
        io.mapOptional("first", funs.first);
        io.mapOptional("second", funs.second);
    }
};
}

// Vector of DiffFunPair to YAML
LLVM_YAML_IS_SEQUENCE_VECTOR(DiffFunPair);

// Overall report: contains pairs of different (non-equal) functions
struct ResultReport {
    std::vector<DiffFunPair> diffFuns;
};

// Report to YAML
namespace llvm::yaml {
template<>
struct MappingTraits<ResultReport> {
    static void mapping(IO &io, ResultReport &result) {
        io.mapOptional("diff-functions", result.diffFuns);
    }
};
}

void reportOutput(Config &config, std::vector<FunPair> &nonequalFuns) {
    ResultReport report;

    for (auto &funPair : nonequalFuns) {
        report.diffFuns.emplace_back(
                FunctionInfo(funPair.first->getName(),
                             getFileForFun(funPair.first),
                             getCallStack(*config.FirstFun, *funPair.first)),
                FunctionInfo(funPair.second->getName(),
                             getFileForFun(funPair.second),
                             getCallStack(*config.SecondFun, *funPair.second))

        );
    }

    llvm::yaml::Output output(outs());
    output << report;
}
