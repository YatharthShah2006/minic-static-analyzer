import os
import sys

# -------------------------------------------------
# Make project root importable
# -------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

from lexer import Lexer
from parser import Parser
from cfg import CFGBuilder


# -------------------------------------------------
# Helpers
# -------------------------------------------------

CFG_DIR = os.path.join(
    os.path.dirname(__file__),
    "construction"
)


def parse_single_function(path):
    with open(path) as f:
        source = f.read()

    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()

    assert len(program.functions) == 1, (
        "CFG construction tests expect exactly one function"
    )

    return program.functions[0]


def build_cfg(path):
    fn = parse_single_function(path)
    return CFGBuilder().build(fn.body)


def has_cycle(cfg):
    """
    Detects whether the CFG contains a cycle
    (used to test loop construction).
    """
    visited = set()
    stack = set()

    def dfs(block):
        if block in stack:
            return True
        if block in visited:
            return False

        visited.add(block)
        stack.add(block)

        for succ in block.successors:
            if dfs(succ):
                return True

        stack.remove(block)
        return False

    return dfs(cfg.entry)


# -------------------------------------------------
# CFG construction tests
# -------------------------------------------------

def test_linear_sequence():
    cfg = build_cfg(os.path.join(CFG_DIR, "linear_sequence.mc"))

    assert cfg.entry is not None
    assert cfg.exit is not None
    assert len(cfg.blocks) == 2

    # Linear code: no block should branch
    for block in cfg.blocks:
        assert len(block.successors) <= 1


def test_if_only():
    cfg = build_cfg(os.path.join(CFG_DIR, "if_only.mc"))
    assert len(cfg.blocks) == 4

    # Exactly one conditional block
    cond_blocks = [b for b in cfg.blocks if len(b.successors) == 2]
    assert len(cond_blocks) == 1

    # There must be exactly one merge point
    merge_blocks = [b for b in cfg.blocks if len(b.predecessors) == 2]
    assert len(merge_blocks) == 1


def test_if_else_shape():
    cfg = build_cfg(os.path.join(CFG_DIR, "if_else_shape.mc"))
    assert len(cfg.blocks) == 5

    cond_blocks = [b for b in cfg.blocks if len(b.successors) == 2]
    assert len(cond_blocks) == 1

    merge_blocks = [b for b in cfg.blocks if len(b.predecessors) == 2]
    assert len(merge_blocks) == 1


def test_while_loop_shape():
    cfg = build_cfg(os.path.join(CFG_DIR, "while_loop_shape.mc"))
    assert len(cfg.blocks) == 5

    # Loop must introduce a cycle
    assert has_cycle(cfg), "Expected a loop cycle in CFG"


def test_nested_if_while():
    cfg = build_cfg(os.path.join(CFG_DIR, "nested_if_while.mc"))

    # Nested control flow → multiple branching points
    branching_blocks = [b for b in cfg.blocks if len(b.successors) >= 2]
    assert len(branching_blocks) >= 2

    # Still must have a cycle (because of while)
    assert has_cycle(cfg)


def test_early_return_shape():
    cfg = build_cfg(os.path.join(CFG_DIR, "early_return_shape.mc"))

    # Blocks containing return statements must terminate control flow
    return_blocks = [
        b for b in cfg.blocks
        if any(stmt.__class__.__name__ == "ReturnStmt" for stmt in b.statements)
    ]

    assert len(return_blocks) >= 2

    for block in return_blocks:
        assert len(block.successors) == 1 and block.successors[0] == cfg.exit, (
            "Return blocks must only have exit as successor"
        )


# -------------------------------------------------
# Main: Run all tests
# -------------------------------------------------

if __name__ == "__main__":
    tests = [
        ("Linear Sequence", test_linear_sequence),
        ("If Only", test_if_only),
        ("If-Else Shape", test_if_else_shape),
        ("While Loop Shape", test_while_loop_shape),
        ("Nested If-While", test_nested_if_while),
        ("Early Return Shape", test_early_return_shape),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            failed += 1

    print("==============================")
    print(f"Results: {passed} passed, {failed} failed")

    # Exit with non-zero code if any tests failed
    sys.exit(0 if failed == 0 else 1)