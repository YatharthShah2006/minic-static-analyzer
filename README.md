# MiniC Static Analyzer

This repository contains an implementation of a **MiniC language front end and static analyzer**, built from first principles.  
The project includes lexical analysis, parsing, semantic analysis, control-flow graph construction, and multiple **CFG-based static analyses**.

The goal of the project is to explore how compilers and static analyzers reason about program behavior using **formal language specifications, control-flow graphs, and dataflow analysis**, rather than ad-hoc or syntax-level checks.

---

## Directory Structure

```
.
├── docs
│   └── language-spec.md     # Formal specification of the MiniC language
├── README.md
└── src
    ├── ast_nodes.py         # AST node definitions
    ├── cfg.py               # Control-flow graph construction
    ├── cfg_analysis.py      # CFG-based static analysis passes
    ├── lexer.py             # Lexical analysis
    ├── parser.py            # Parsing and AST construction
    ├── pipeline.py          # End-to-end analysis pipeline / driver
    ├── semantic.py          # Semantic analysis
    ├── symbols.py           # Symbol table and scope handling
    └── tokens.py            # Token definitions
```

---

## MiniC Language Specification

MiniC is a simplified, C-like language designed to support compiler and static analysis experimentation.

The full language definition—including:
- Grammar and syntax
- Type system
- Scoping and symbol rules
- Function semantics
- Control-flow constructs

is specified in **`docs/language-spec.md`**.  
All components of the toolchain are implemented to conform strictly to this specification.

---

## Compilation and Analysis Pipeline

The MiniC toolchain follows a structured pipeline implemented in `pipeline.py`:

```
Source Code
   ↓
Lexer
   ↓
Parser
   ↓
Abstract Syntax Tree (AST)
   ↓
Semantic Analysis
   ↓
Control-Flow Graph (CFG) Construction
   ↓
CFG-Based Static Analysis
```

Each stage is implemented as an independent module with a clear separation of responsibilities.

---

## Semantic Analysis

The semantic analyzer performs:
- Name resolution and scope checking
- Symbol table construction
- Type checking
- Validation of function return behavior

Function return correctness is enforced using a **CFG-based return path analysis**, ensuring that all execution paths return a value when required. This replaces earlier syntax-level return checks and correctly handles nested conditionals and loops.

---

## Control-Flow Graph Construction

For each function, a control-flow graph is constructed in `cfg.py`:

- Nodes correspond to basic blocks
- Edges represent possible control-flow transfers
- Entry and exit blocks are explicitly modeled

The CFG serves as the foundation for all subsequent static analyses.

---

## Static Analysis Framework

The static analysis framework is implemented in `cfg_analysis.py` and operates directly over control-flow graphs.

All analyses are implemented using:
- Explicit lattice definitions
- Transfer functions per CFG node
- Fixed-point iteration until convergence

### Implemented Analyses

#### Return Path Analysis
Ensures that all execution paths in a function return a value when required.

---

#### Unreachable Code Detection
Detects statements that are provably unreachable at runtime.

**Examples**
```c
return 0;
x = 5;   // unreachable
```

```c
if (0) {
    foo(); // unreachable
}
```

**Technique**
- Reachability analysis over the CFG
- DFS from function entry
- Reports AST nodes mapped to unreachable basic blocks

---

#### Definite Assignment Analysis
Detects use-before-assignment errors.

**Example**
```c
int x;
if (cond) {
    x = 5;
}
print(x); // error: x may be uninitialized
```

**Technique**
- Forward dataflow analysis
- Lattice: sets of definitely assigned variables
- Join operation: intersection

---

#### Dead Store Detection
Detects assignments whose values are never subsequently read.

**Example**
```c
x = 10;
x = 20;  // dead store
print(x);
```

**Technique**
- Backward dataflow analysis
- Live variable tracking

---

#### Path-Sensitive Zero / Null Analysis

Performs **path-sensitive abstract interpretation** to detect unsafe operations involving zero (or null-like) values using a control-flow graph.

**Example**

    if (x) {
        y = 10 / x; // safe on this path (x is non-zero)
    }

    y = 10 / x; // warning: x may be zero

**Technique**
- Forward data-flow analysis over a **CFG with edge-annotated control flow**
- Tracks abstract states (`ZERO`, `NONZERO`, `UNKNOWN`) per variable
- **Refines abstract state on conditional branches** (e.g. `if (x)`, `if (!x)`, `while (x)`)
- Conservatively merges states at control-flow join points
- Reports errors only when an unsafe operation is **possible on some feasible execution path**

---

## Design Principles

- Strict separation between parsing, semantics, CFG construction, and analysis
- Soundness-first approach (may produce false positives, never false negatives)
- Explicit distinction between forward, backward, and path-sensitive analyses
- CFG-based reasoning instead of local or syntactic checks

---

## How to Run

1. Clone the repository:
```bash
git clone <repository-url>
cd Static_Analyzer_for_MiniC
```
a
2. Run the analysis pipeline on a MiniC source file:
```bash
python src/pipeline.py path/to/program.mc
```

3. The tool will:
- Parse the program
- Perform semantic analysis
- Build the control-flow graph
- Run all static analysis passes
- Report warnings and errors with source locations

---

## Motivation

This project is an exploration of how real-world compilers and static analyzers detect subtle semantic bugs using **formal language specifications, control-flow graphs, and dataflow analysis**, rather than relying on ad-hoc or syntax-level checks.

---

## Possible Extensions

The current design intentionally focuses on **sound, intraprocedural analysis** with a clean separation between CFG construction and analysis passes. The architecture naturally supports the following extensions:

- **Interprocedural Analysis**  
  Extend the analyzer across function boundaries using function summaries (e.g. return value properties, side effects). This would allow reasoning about safety properties across calls without inlining.

- **General Abstract Interpretation Framework**  
  Generalize the existing analyses into a reusable framework with pluggable abstract domains (lattices). This would enable adding new analyses (e.g. nullness, bounds, taint) with minimal changes to the core infrastructure.

- **Loop Invariant and Widening Techniques**  
  Improve precision and convergence in loops by adding loop invariants or widening/narrowing strategies, enabling more precise reasoning about values across iterations.

- **Optimization-Oriented Analyses**  
  Leverage existing analyses (definite assignment, dead store detection, CFG reasoning) to drive optimization passes such as dead code elimination or redundant assignment removal.

These extensions build directly on the current CFG-based architecture and can be added incrementally without redesigning the core pipeline.