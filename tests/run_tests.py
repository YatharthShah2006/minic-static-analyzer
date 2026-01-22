import os
import sys
import subprocess


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DIAGNOSTIC_RUNNER = os.path.join(
    ROOT, "tests", "diagnostics", "run_diagnostics.py"
)

CFG_TEST_RUNNER = "tests/cfg/test_cfg_construction.py"


def run_diagnostics():
    print("\n==============================")
    print("Running diagnostic tests")
    print("==============================")

    result = subprocess.run(
        [sys.executable, DIAGNOSTIC_RUNNER],
        cwd=ROOT
    )

    return result.returncode == 0


def run_cfg_tests():
    print("\n==============================")
    print("Running CFG construction tests")
    print("==============================")

    result = subprocess.run(
        [sys.executable, CFG_TEST_RUNNER],
        cwd=ROOT
    )

    return result.returncode == 0


def main():
    ok = True

    if not run_diagnostics():
        ok = False

    if not run_cfg_tests():
        ok = False

    print("\n==============================")
    if ok:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
