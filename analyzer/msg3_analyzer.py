"""
msg3_analyzer.py

Business logic for MSG3 success-rate analysis.

Responsibilities:
    - Classify MSG3 records as success, failure, or ignored.
    - Calculate MSG3 success rate.
    - Apply the configured success-rate threshold.
    - Return a machine-readable analysis result.

This module does NOT:
    - Read log files.
    - Parse raw log lines.
    - Generate reports.
    - Print output.
"""

from typing import Dict, List, Optional

from analyzer.constants import (
    DEFAULT_SUCCESS_THRESHOLD,
    FAILURE_STATUS,
    SUCCESS_STATUS,
)

from analyzer.models import Msg3Record


class Msg3Analyzer:
    """
    Analyzer responsible for calculating MSG3 success rate.

    Success-rate formula:

        successes
        ---------------------------- × 100
        successes + failures

    Ignored records are excluded from the denominator.
    """

    def __init__(
        self,
        success_threshold: float = DEFAULT_SUCCESS_THRESHOLD,
    ) -> None:
        """
        Initialize the analyzer.

        Parameters
        ----------
        success_threshold:
            Minimum success rate required for PASS.

        Example
        -------
        95.0 means:

            rate >= 95.0  -> PASS
            rate <  95.0  -> FAIL
        """

        if not 0 <= success_threshold <= 100:
            raise ValueError(
                "success_threshold must be between 0 and 100"
            )

        self.success_threshold = success_threshold

        # Counters
        self.success = 0
        self.failure = 0
        self.ignored = 0

    # ==========================================================
    # PUBLIC METHOD
    # ==========================================================

    def analyze(
        self,
        records: List[Msg3Record],
    ) -> Dict[str, object]:
        """
        Analyze parsed MSG3 records.

        Parameters
        ----------
        records:
            List of Msg3Record objects produced by LogParser.

        Returns
        -------
        Dict[str, object]
            Machine-readable analysis result.
        """

        # Reset counters so the same analyzer instance
        # can safely be reused.
        self._reset_counters()

        for record in records:
            self._classify_record(record)

        return self.build_result()

    # ==========================================================
    # RECORD CLASSIFICATION
    # ==========================================================

    def _classify_record(
        self,
        record: Msg3Record,
    ) -> None:
        """
        Classify a single MSG3 record.

        Rules
        -----
        Success status -> success

        Failure status -> failure

        Anything else -> ignored
        """

        status = self._normalize_status(record.status)

        if status in SUCCESS_STATUS:

            self.success += 1

        elif status in FAILURE_STATUS:

            self.failure += 1

        else:

            self.ignored += 1

    # ==========================================================
    # STATUS NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_status(
        status: Optional[str],
    ) -> str:
        """
        Normalize status before classification.

        Examples
        --------
        "SUCCESS" -> "success"
        "Success" -> "success"
        " success " -> "success"
        """

        if status is None:
            return ""

        return status.strip().lower()

    # ==========================================================
    # SUCCESS RATE
    # ==========================================================

    def calculate_success_rate(self) -> Optional[float]:
        """
        Calculate MSG3 success rate.

        Formula:

            successes
            ---------------------------- × 100
            successes + failures

        Ignored records are NOT included in the denominator.

        Returns
        -------
        Optional[float]

            Example:
                51 successes
                26 failures

                -> 66.23

            If there are no measurable records:

                -> None
        """

        measurable_records = (
            self.success + self.failure
        )

        # Empty measurable dataset.
        #
        # We deliberately return None instead of 0.
        # 0% means there were attempts and all failed.
        # None means there was nothing measurable.
        if measurable_records == 0:
            return None

        success_rate = (
            self.success
            / measurable_records
        ) * 100

        return round(success_rate, 2)

    # ==========================================================
    # QUALITY STATUS
    # ==========================================================

    def quality_status(self) -> str:
        """
        Determine PASS / FAIL / NO_DATA.

        Rules
        -----
        rate is None
            -> NO_DATA

        rate >= threshold
            -> PASS

        rate < threshold
            -> FAIL
        """

        rate = self.calculate_success_rate()

        if rate is None:
            return "NO_DATA"

        if rate >= self.success_threshold:
            return "PASS"

        return "FAIL"

    # ==========================================================
    # BUILD RESULT
    # ==========================================================

    def build_result(self) -> Dict[str, object]:
        """
        Build final machine-readable result.

        This dictionary is consumed by:
            - report.py
            - Part 3 quality gate
            - automated tests
        """

        total_records = (
            self.success
            + self.failure
            + self.ignored
        )

        return {
            "total_records": total_records,
            "successes": self.success,
            "failures": self.failure,
            "ignored": self.ignored,
            "success_rate": self.calculate_success_rate(),

            # IMPORTANT:
            # This field fixes the KeyError that
            # your test was reporting.
            "success_threshold": self.success_threshold,

            "quality_status": self.quality_status(),
        }

    # ==========================================================
    # RESET
    # ==========================================================

    def _reset_counters(self) -> None:
        """
        Reset counters before each analysis.

        This makes the analyzer reusable.
        """

        self.success = 0
        self.failure = 0
        self.ignored = 0