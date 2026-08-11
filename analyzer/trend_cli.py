import argparse
import sys

from analyzer.parser import LogParser
from analyzer.trend_analyzer import HourlyTrendAnalyzer


def build_parser():
    """
    Build command-line arguments for the
    hourly trend and degradation analysis.
    """

    parser = argparse.ArgumentParser(
        description="MSG3 Hourly Trend Analyzer"
    )

    parser.add_argument(
        "--log",
        required=True,
        help="Path to the MSG3 log file"
    )

    parser.add_argument(
        "--degradation-threshold",
        type=float,
        default=10.0,
        help=(
            "Minimum percentage-point drop between "
            "consecutive hours to report degradation. "
            "Default: 10.0"
        )
    )

    return parser


def main():
    """
    Execute hourly trend and degradation analysis.
    """

    parser = build_parser()
    args = parser.parse_args()

    try:
        # --------------------------------------------
        # 1. Parse log
        # --------------------------------------------

        log_parser = LogParser(args.log)

        records = log_parser.parse()

        # --------------------------------------------
        # 2. Run hourly trend analysis
        # --------------------------------------------

        analyzer = HourlyTrendAnalyzer(
            degradation_threshold=(
                args.degradation_threshold
            )
        )

        result = analyzer.analyze(records)

        # --------------------------------------------
        # 3. Print hourly trend
        # --------------------------------------------

        print()
        print("=" * 70)
        print("MSG3 HOURLY SUCCESS-RATE TREND")
        print("=" * 70)

        hourly_trend = result["hourly_trend"]

        if not hourly_trend:

            print(
                "No measurable MSG3 records found."
            )

        else:

            print(
                f"{'Hour':20} "
                f"{'Success':>10} "
                f"{'Failure':>10} "
                f"{'Rate':>10}"
            )

            print("-" * 70)

            for hour in hourly_trend:

                success_rate = hour[
                    "success_rate"
                ]

                if success_rate is None:
                    rate = "N/A"
                else:
                    rate = (
                        f"{success_rate:.2f}%"
                    )

                print(
                    f"{hour['hour']:20} "
                    f"{hour['successes']:>10} "
                    f"{hour['failures']:>10} "
                    f"{rate:>10}"
                )

        # --------------------------------------------
        # 4. Print degradation information
        # --------------------------------------------

        print()
        print("=" * 70)
        print("MSG3 DEGRADATION ANALYSIS")
        print("=" * 70)

        print(
            "Degradation Threshold : "
            f"{result['degradation_threshold']:.2f} "
            "percentage points"
        )

        degradation_windows = (
            result["degradation_windows"]
        )

        if not degradation_windows:

            print()
            print(
                "No significant degradation detected."
            )

        else:

            print()

            for index, window in enumerate(
                degradation_windows,
                start=1
            ):

                print(
                    f"Degradation Window #{index}"
                )

                print(
                    f"From Hour       : "
                    f"{window['from_hour']}"
                )

                print(
                    f"To Hour         : "
                    f"{window['to_hour']}"
                )

                print(
                    f"Previous Rate   : "
                    f"{window['previous_success_rate']:.2f}%"
                )

                print(
                    f"Current Rate    : "
                    f"{window['current_success_rate']:.2f}%"
                )

                print(
                    f"Drop            : "
                    f"{window['drop_percentage_points']:.2f} "
                    "percentage points"
                )

                print("-" * 70)

        return 0

    except FileNotFoundError as exc:

        print(
            f"ERROR: {exc}",
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
            f"ERROR: {exc}",
            file=sys.stderr
        )

        return 2


if __name__ == "__main__":
    sys.exit(main())