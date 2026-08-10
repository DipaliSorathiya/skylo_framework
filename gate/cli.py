import argparse
import sys

from analyzer.parser import LogParser
from gate.quality_gate import QualityGate


def build_parser():
    """
    Build command-line argument parser.
    """

    parser = argparse.ArgumentParser(
        description=(
            "MSG3 Quality Gate - "
            "Fail the build when MSG3 success rate "
            "falls below the configured threshold."
        )
    )

    parser.add_argument(
        "--log",
        required=True,
        help="Path to the log file to analyze."
    )

    parser.add_argument(
        "--min-rate",
        type=float,
        required=True,
        help=(
            "Minimum acceptable MSG3 success rate "
            "in percentage. Example: 95"
        )
    )

    return parser


def main() -> int:
    """
    Execute the quality gate.

    Returns:
        0 when gate passes.
        1 when gate fails.
        2 for invalid input/configuration errors.
    """

    parser = build_parser()

    args = parser.parse_args()

    try:
        # ---------------------------------------------------------
        # Step 1: Parse log
        # ---------------------------------------------------------

        log_parser = LogParser(args.log)

        records = log_parser.parse()

        # ---------------------------------------------------------
        # Step 2: Evaluate quality gate
        # ---------------------------------------------------------

        gate = QualityGate(
            minimum_success_rate=args.min_rate
        )

        result = gate.evaluate(records)

        # ---------------------------------------------------------
        # Step 3: Human-readable output
        # ---------------------------------------------------------

        print()
        print("=" * 60)
        print("MSG3 QUALITY GATE")
        print("=" * 60)

        print(
            f"Log File       : {args.log}"
        )

        print(
            f"Successes      : {result['successes']}"
        )

        print(
            f"Failures       : {result['failures']}"
        )

        print(
            f"Ignored        : {result['ignored']}"
        )

        print(
            f"Success Rate   : "
            f"{result['success_rate']:.2f}%"
        )

        print(
            f"Minimum Rate   : "
            f"{result['success_threshold']:.2f}%"
        )

        print(
            f"Gate Status    : "
            f"{result['gate_status']}"
        )

        print("=" * 60)

        # ---------------------------------------------------------
        # Step 4: Meaningful exit code
        # ---------------------------------------------------------

        if result["gate_passed"]:
            return 0

        return 1

    except FileNotFoundError:
        print(
            f"ERROR: Log file not found: {args.log}",
            file=sys.stderr
        )

        return 2

    except ValueError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr
        )

        return 2

    except Exception as exc:
        print(
            f"ERROR: Quality gate execution failed: {exc}",
            file=sys.stderr
        )

        return 2


if __name__ == "__main__":
    sys.exit(main())