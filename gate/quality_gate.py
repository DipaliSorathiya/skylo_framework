from typing import Dict, List

from analyzer.models import Msg3Record
from analyzer.msg3_analyzer import Msg3Analyzer


class QualityGate:
    """
    Quality Gate for MSG3 success rate.

    The QualityGate reuses Msg3Analyzer from Part 1.

    Responsibilities:
        - Analyze parsed MSG3 records
        - Compare success rate against a minimum threshold
        - Return a structured result
        - Determine whether the build should pass or fail

    This class does not parse log files.
    """

    def __init__(
        self,
        minimum_success_rate: float
    ):
        """
        Args:
            minimum_success_rate:
                Minimum acceptable MSG3 success rate.
                Example: 95.0 means 95%.
        """

        if not 0 <= minimum_success_rate <= 100:
            raise ValueError(
                "minimum_success_rate must be between 0 and 100"
            )

        self.minimum_success_rate = minimum_success_rate

        # Reuse Part 1 analyzer.
        self.analyzer = Msg3Analyzer()

    def evaluate(
        self,
        records: List[Msg3Record]
    ) -> Dict:
        """
        Evaluate parsed MSG3 records against the threshold.

        Args:
            records:
                Parsed MSG3 records from LogParser.

        Returns:
            Dictionary containing analysis and gate result.
        """

        result = self.analyzer.analyze(records)

        success_rate = result["success_rate"]

        # ---------------------------------------------------------
        # Empty / non-measurable input
        # ---------------------------------------------------------

        if success_rate is None:
            gate_passed = False
        else:
            gate_passed = (
                success_rate >= self.minimum_success_rate
            )

        return {
            "successes": result["successes"],
            "failures": result["failures"],
            "ignored": result["ignored"],
            "success_rate": success_rate,
            "success_threshold": self.minimum_success_rate,
            "gate_status": (
                "PASS"
                if gate_passed
                else "FAIL"
            ),
            "gate_passed": gate_passed
        }