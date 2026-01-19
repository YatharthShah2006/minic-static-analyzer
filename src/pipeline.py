from typing import List

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer, SemanticError
from cfg import CFGBuilder
from cfg_analysis import *
from ast_nodes import Program


class AnalysisResult:
    def __init__(self):
        self.errors: List[SemanticError] = []


    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def report(self):
        for e in self.errors:
            print(e)


# -------------------------
# Main pipeline
# -------------------------

def analyze_source(source: str) -> AnalysisResult:
    result = AnalysisResult()

    # -------------------------
    # 1. Lexing
    # -------------------------
    try:
        tokens = Lexer(source).tokenize()
    except Exception as e:
        print("Lexer error:", e)
        return result

    # -------------------------
    # 2. Parsing
    # -------------------------
    try:
        parser = Parser(tokens)
        program: Program = parser.parse()
    except Exception as e:
        print("Parser error:", e)
        return result

    # -------------------------
    # 3. Semantic analysis
    # -------------------------
    sem = SemanticAnalyzer()
    sem_errors = sem.analyze(program)
    result.errors.extend(sem_errors)

    # -------------------------
    # 4. CFG-based analyses
    # -------------------------
    # We run these even if semantic errors exist,
    # so we can report more diagnostics in one go.
    for fn in program.functions:
        try:
            cfg = CFGBuilder().build(fn.body)
            ret_analyzer = CFGReturnAnalyzer(cfg)
            if not ret_analyzer.function_always_returns():
                result.errors.append(
                    SemanticError(
                        f"Function '{fn.name}' may not return a value on all paths",
                        fn
                    )
                )
            
            ua = CFGUnreachableAnalyzer(cfg)
            for block in ua.unreachable_blocks():
                for stmt in block.statements:
                    result.errors.append(
                        SemanticError("Unreachable code", stmt)
                    )

            da = CFGDefiniteAssignmentAnalyzer(cfg)
            da.analyze()
            da.check_uses()
            result.errors.extend(da.errors)

            ds = CFGDeadStoreAnalyzer(cfg)
            ds.analyze()

            for stmt in ds.dead_stores:
                result.errors.append(
                    SemanticError("Dead store", stmt)
                )

            
        except Exception as e:
            # internal compiler error in CFG phase
            print(f"CFG error in function '{fn.name}':", e)

    return result


# -------------------------
# CLI entry point
# -------------------------

def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <source-file>")
        return

    with open(sys.argv[1]) as f:
        source = f.read()

    result = analyze_source(source)

    if result.has_errors():
        print("❌ Errors found:")
        result.report()
    else:
        print("✅ No errors found.")


if __name__ == "__main__":
    main()
