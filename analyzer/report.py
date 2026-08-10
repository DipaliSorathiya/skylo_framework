"""
report.py

Generates reports for MSG3 analysis.

Responsibilities
----------------
1. Print console report
2. Save JSON report
"""

import json
from pathlib import Path
from datetime import datetime


class ReportGenerator:

    def __init__(self, output_file="reports/msg3_report.json"):

        self.output_file = Path(output_file)

        # Create reports folder if missing
        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    # ----------------------------------------------------

    def print_console(self, result: dict):

        print()

        print("=" * 60)
        print("             MSG3 SUCCESS RATE REPORT")
        print("=" * 60)

        print(f"Total Records : {result['total_records']}")
        print(f"Successes     : {result['successes']}")
        print(f"Failures      : {result['failures']}")
        print(f"Ignored       : {result['ignored']}")
        print(f"Success Rate  : {result['success_rate']} %")
        print(f"Quality Gate  : {result['quality_status']}")

        print("=" * 60)

    # ----------------------------------------------------

    def save_json(self, result: dict):

        report = {

            "generated_at": datetime.utcnow().isoformat(),

            **result

        }

        with open(
            self.output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                indent=4
            )

        print()

        print(
            f"JSON report generated -> {self.output_file}"
        )