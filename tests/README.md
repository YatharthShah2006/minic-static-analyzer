# Tests

## Running All Tests
```bash
python tests/run_tests.py
```

This runs:
- Diagnostic tests (lexer, parser, semantic, analysis)
- CFG construction tests
- All test suites in the project

## Test Structure

- `analysis/` - Dataflow analysis tests (dead store, null analysis, etc.)
- `cfg/` - Control Flow Graph construction tests
- `lexer/` - Lexer error tests
- `parser/` - Parser error tests
- `semantic/` - Semantic analysis tests
- `valid/` - Valid programs that should compile without errors
- `diagnostics/run_diagnostics.py` - Individual diagnostic test runner
- `run_tests.py` - **Main test runner (use this)**

## Test File Format

Test files use special comments to specify expected behavior:
```c
// EXPECT: OK
// or
// EXPECT: error message substring
```