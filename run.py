import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run_command(command):
    """
    Execute a command and return its exit code.
    """

    print()
    print("=" * 70)
    print("Running:")
    print(" ".join(str(item) for item in command))
    print("=" * 70)

    result = subprocess.run(command)

    return result.returncode


def run_tests():
    """
    Run the complete pytest suite.
    """

    return run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-v"
        ]
    )


def run_quality_gate(
    log_file,
    minimum_success_rate
):
    """
    Run the MSG3 quality gate.
    """

    return run_command(
        [
            sys.executable,
            "-m",
            "gate.cli",
            "--log",
            str(log_file),
            "--min-rate",
            str(minimum_success_rate)
        ]
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run the QA automation framework."
        )
    )

    parser.add_argument(
        "--log",
        required=True,
        help="Log file to use for the MSG3 quality gate."
    )

    parser.add_argument(
        "--min-rate",
        type=float,
        default=95.0,
        help=(
            "Minimum acceptable MSG3 success rate. "
            "Default: 95.0"
        )
    )

    args = parser.parse_args()

    log_file = Path(args.log)

    # ------------------------------------------------------------
    # Step 1 - Validate log
    # ------------------------------------------------------------

    if not log_file.exists():

        print(
            f"ERROR: Log file does not exist: {log_file}",
            file=sys.stderr
        )

        return 2

    # ------------------------------------------------------------
    # Step 2 - Run tests
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 1 - AUTOMATED TEST SUITE")
    print("=" * 70)

    test_exit_code = run_tests()

    if test_exit_code != 0:

        print()
        print("TEST SUITE FAILED")

        return test_exit_code

    # ------------------------------------------------------------
    # Step 3 - Run Quality Gate
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 2 - MSG3 QUALITY GATE")
    print("=" * 70)

    gate_exit_code = run_quality_gate(
        log_file,
        args.min_rate
    )

    # ------------------------------------------------------------
    # Step 4 - Final result
    # ------------------------------------------------------------

    if gate_exit_code == 0:

        print()
        print("=" * 70)
        print("FRAMEWORK RESULT: PASS")
        print("=" * 70)

        return 0

    if gate_exit_code == 1:

        print()
        print("=" * 70)
        print("FRAMEWORK RESULT: QUALITY GATE FAILED")
        print("=" * 70)

        return 1

    print()
    print("=" * 70)
    print("FRAMEWORK RESULT: EXECUTION ERROR")
    print("=" * 70)

    return 2


if __name__ == "__main__":
    sys.exit(main())