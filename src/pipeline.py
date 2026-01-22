from typing import List
import os
from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer, SemanticError, Diagnostic
from program_semantic import ProgramSemanticChecker
from cfg import CFGBuilder
from cfg_analysis import *
from ast_nodes import Program


class AnalysisResult:
    def __init__(self):
        self.errors: List[Diagnostic] = []


    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def report(self):
        for e in self.errors:
            print(e)


# -------------------------
# Main pipeline
# -------------------------

def analyze_file(path: str) -> AnalysisResult:
    with open(path) as f:
        source = f.read()

    return analyze_source(source)

def collect_mc_files(path: str) -> list[str]:
    mc_files = []

    if os.path.isfile(path):
        if path.endswith(".mc"):
            mc_files.append(path)
        return mc_files

    for root, _, files in os.walk(path):
        for name in files:
            if name.endswith(".mc"):
                mc_files.append(os.path.join(root, name))

    return sorted(mc_files)

def analyze_source(source: str) -> AnalysisResult:
    result = AnalysisResult()

    # -------------------------
    # 1. Lexing
    # -------------------------
    try:
        tokens = Lexer(source).tokenize()
    except LexerError as e:
        result.errors.append(Diagnostic(str(e)))
        return result

    # -------------------------
    # 2. Parsing
    # -------------------------
    try:
        parser = Parser(tokens)
        program: Program = parser.parse()
    except ParseError as e:
        result.errors.append(Diagnostic(str(e)))
        return result

    # -------------------------
    # 3. Semantic analysis
    # -------------------------
    sem = SemanticAnalyzer()
    sem_errors = sem.analyze(program)
    result.errors.extend(sem_errors)

    # -------------------------
    # 3.5 Program-level semantics
    # -------------------------
    prog_checker = ProgramSemanticChecker()
    prog_errors = prog_checker.check(program)
    result.errors.extend(prog_errors)

    # If main() is invalid or missing, stop here
    if prog_errors:
        return result

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

            da = CFGDefiniteAssignmentAnalyzer(cfg, fn.params)
            da.analyze()
            da.check_uses()
            result.errors.extend(da.errors)

            ds = CFGDeadStoreAnalyzer(cfg)
            ds.analyze()

            for stmt in ds.dead_stores:
                result.errors.append(
                    SemanticError("Dead store", stmt)
                )

            null = CFGZeroAnalysis(cfg)
            null.analyze()

            for e in null.errors:
                result.errors.append(e)

            
        except Exception as e:
            # internal compiler error in CFG phase
            print(f"CFG error in function '{fn.name}':", e)

    return result


# -------------------------
# CLI entry point
# -------------------------

def main():
    import sys
    import os

    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <file.mc | directory>")
        return

    path = sys.argv[1]

    mc_files = collect_mc_files(path)

    if not mc_files:
        print("No .mc files found.")
        return

    total = 0
    failed = 0

    for file_path in mc_files:
        total += 1
        print(f"\n=== Analyzing {file_path} ===")

        try:
            result = analyze_file(file_path)
        except Exception as e:
            print("❌ Internal error:", e)
            failed += 1
            continue

        if result.has_errors():
            failed += 1
            print("❌ Errors found:")
            result.report()
        else:
            print("✅ No errors found.")

    print("\n==============================")
    print(f"Analyzed {total} file(s)")
    print(f"Passed: {total - failed}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()
