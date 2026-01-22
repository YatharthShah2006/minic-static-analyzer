import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

from pipeline import analyze_source


# ---------------------------------------
# Configuration
# ---------------------------------------

TEST_EXT = ".mc"
EXPECT_PREFIX = "// EXPECT:"

# Default test directory relative to this script
DEFAULT_TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Directories to exclude from testing
EXCLUDE_DIRS = {"cfg", "__pycache__"}


# ---------------------------------------
# Helpers
# ---------------------------------------

def extract_expectations(source: str):
    """
    Extract EXPECT directives from source.
    Returns a list of expected strings.
    """
    expects = []
    for line in source.splitlines():
        line = line.strip()
        if line.startswith(EXPECT_PREFIX):
            expects.append(line[len(EXPECT_PREFIX):].strip())
    return expects


def run_single_test(path: str) -> bool:
    """
    Run analyzer on one file and compare diagnostics.
    Returns True if test passes, False otherwise.
    """
    print(f"=== Analyzing {path} ===")

    with open(path) as f:
        source = f.read()

    expected = extract_expectations(source)

    # Always run the analyzer (even if EXPECT is missing)
    result = analyze_source(source)
    actual = [str(e).strip() for e in result.errors]

    # -------------------------
    # Test specification error
    # -------------------------
    if not expected:
        print("❌ TEST ERROR: no EXPECT directives found")
        if actual:
            print("Analyzer produced diagnostics:")
            for a in actual:
                print(f"  {a}")
        return False

    # -------------------------
    # EXPECT: OK
    # -------------------------
    if expected == ["OK"]:
        if actual:
            print("❌ FAIL: expected no diagnostics, but got:")
            for a in actual:
                print(f"  {a}")
            return False

        print("✅ PASS")
        return True

    # -------------------------
    # Error expectation matching
    # -------------------------
    expected_norm = [e.strip().lower() for e in expected]
    actual_lower = [a.lower() for a in actual]
    
    missing = []
    unexpected = []

    # Check if each expected string appears as a substring in at least one actual diagnostic
    for i, e in enumerate(expected_norm):
        if not any(e in a_lower for a_lower in actual_lower):
            missing.append(expected[i].strip())  # Show original case in error message

    # Check if each actual diagnostic matches at least one expected pattern
    for i, a_lower in enumerate(actual_lower):
        if not any(e in a_lower for e in expected_norm):
            unexpected.append(actual[i])  # Show original case in error message

    if missing or unexpected:
        print("❌ FAIL")

        if missing:
            print("Missing expected diagnostics:")
            for m in missing:
                print(f"  {m}")

        if unexpected:
            print("Unexpected diagnostics:")
            for u in unexpected:
                print(f"  {u}")

        return False

    print("✅ PASS")
    return True

def should_skip_directory(dirpath: str) -> bool:
    """
    Check if directory should be skipped based on its name.
    """
    dir_name = os.path.basename(dirpath)
    return dir_name in EXCLUDE_DIRS


def run_tests(root: str):
    """
    Run all tests under root directory.
    Returns (total_tests, failed_tests).
    """
    total = 0
    failures = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        if should_skip_directory(dirpath):
            continue
        
        # Remove excluded directories from dirnames to prevent os.walk from entering them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for name in filenames:
            if name.endswith(TEST_EXT):
                total += 1
                path = os.path.join(dirpath, name)
                if not run_single_test(path):
                    failures += 1

    return total, failures


# ---------------------------------------
# Entry point
# ---------------------------------------

def main():
    # Use provided directory or default to the tests directory
    if len(sys.argv) > 2:
        print("Usage: python run_diagnostics.py [tests-directory]")
        print("If no directory provided, uses the current tests directory")
        sys.exit(1)
    
    root = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_TEST_DIR
    
    print(f"Running tests from: {root}")
    print(f"Excluding directories: {', '.join(EXCLUDE_DIRS)}")
    print()
    
    total, failed = run_tests(root)
    passed = total - failed

    print("\n==============================")
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()