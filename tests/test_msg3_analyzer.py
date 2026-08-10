"""
Unit tests for MSG3 analyzer.

The analyzer is responsible for:

- Classifying success records
- Classifying failure records
- Ignoring unknown statuses
- Calculating MSG3 success rate
- Handling empty input
- Applying the configured quality threshold
"""

from analyzer.models import Msg3Record
from analyzer.msg3_analyzer import Msg3Analyzer


def create_record(status):
    """
    Create a minimal Msg3Record for testing.

    Keeping record creation in one helper makes
    the actual test cases easier to read.
    """

    return Msg3Record(
        timestamp="2024-04-24 10:00:00",
        rnti="100",
        message_type="MSG3-RRC-C-REQ",
        status=status,
    )


class TestMsg3Analyzer:

    def test_all_success(self):
        """
        3 successes / 3 measurable records = 100%.
        """

        records = [
            create_record("success"),
            create_record("success"),
            create_record("success"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["total_records"] == 3
        assert result["successes"] == 3
        assert result["failures"] == 0
        assert result["ignored"] == 0
        assert result["success_rate"] == 100.0
        assert result["quality_status"] == "PASS"

    def test_all_failures(self):
        """
        0 successes / 3 measurable records = 0%.
        """

        records = [
            create_record("timeout"),
            create_record("failure"),
            create_record("crc-error"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["total_records"] == 3
        assert result["successes"] == 0
        assert result["failures"] == 3
        assert result["ignored"] == 0
        assert result["success_rate"] == 0.0
        assert result["quality_status"] == "FAIL"

    def test_mixed_success_and_failure(self):
        """
        2 successes / (2 successes + 2 failures)
        = 50%.
        """

        records = [
            create_record("success"),
            create_record("success"),
            create_record("failure"),
            create_record("timeout"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["total_records"] == 4
        assert result["successes"] == 2
        assert result["failures"] == 2
        assert result["ignored"] == 0
        assert result["success_rate"] == 50.0
        assert result["quality_status"] == "FAIL"

    def test_ignored_status(self):
        """
        Unknown statuses should be ignored.

        They must NOT be included in the success-rate
        denominator.
        """

        records = [
            create_record("success"),
            create_record("pending"),
            create_record("failure"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["total_records"] == 3
        assert result["successes"] == 1
        assert result["failures"] == 1
        assert result["ignored"] == 1

        # 1 / (1 + 1) * 100 = 50%
        assert result["success_rate"] == 50.0

    def test_empty_records(self):
        """
        No measurable MSG3 records should produce
        NO_DATA rather than 0% or 100%.
        """

        result = Msg3Analyzer().analyze([])

        assert result["total_records"] == 0
        assert result["successes"] == 0
        assert result["failures"] == 0
        assert result["ignored"] == 0
        assert result["success_rate"] is None
        assert result["quality_status"] == "NO_DATA"

    def test_success_rate_precision(self):
        """
        2 successes / 3 measurable records
        = 66.67%.
        """

        records = [
            create_record("success"),
            create_record("success"),
            create_record("failure"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["success_rate"] == 66.67

    def test_quality_gate_fail_below_threshold(self):
        """
        Current threshold = 95%.

        9 successes / 10 measurable records = 90%.
        Therefore the result must FAIL.
        """

        records = [
            create_record("success")
            for _ in range(9)
        ]

        records.append(create_record("failure"))

        result = Msg3Analyzer().analyze(records)

        assert result["success_rate"] == 90.0
        assert result["success_threshold"] == 95.0
        assert result["quality_status"] == "FAIL"

    def test_quality_gate_pass_at_threshold(self):
        """
        Current threshold = 95%.

        19 successes / 20 measurable records = 95%.

        Boundary condition:
        rate == threshold should PASS.
        """

        records = [
            create_record("success")
            for _ in range(19)
        ]

        records.append(create_record("failure"))

        result = Msg3Analyzer().analyze(records)

        assert result["success_rate"] == 95.0
        assert result["success_threshold"] == 95.0
        assert result["quality_status"] == "PASS"

    def test_case_normalization(self):
        """
        Status matching should be case-insensitive.
        """

        records = [
            create_record("SUCCESS"),
            create_record("Success"),
            create_record("success"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["successes"] == 3
        assert result["failures"] == 0
        assert result["success_rate"] == 100.0

    def test_ignored_records_do_not_affect_rate(self):
        """
        Ignored records must not affect the denominator.

        2 successes
        1 failure
        2 ignored

        Success rate:

            2 / (2 + 1) * 100

        = 66.67%
        """

        records = [
            create_record("success"),
            create_record("success"),
            create_record("failure"),
            create_record("unknown"),
            create_record("pending"),
        ]

        result = Msg3Analyzer().analyze(records)

        assert result["total_records"] == 5
        assert result["successes"] == 2
        assert result["failures"] == 1
        assert result["ignored"] == 2
        assert result["success_rate"] == 66.67

    def test_analyzer_can_be_reused(self):
        """
        The analyzer should reset its counters before
        every analyze() call.
        """

        analyzer = Msg3Analyzer()

        first_records = [
            create_record("success"),
            create_record("failure"),
        ]

        first_result = analyzer.analyze(first_records)

        assert first_result["successes"] == 1
        assert first_result["failures"] == 1
        assert first_result["success_rate"] == 50.0

        second_records = [
            create_record("success"),
            create_record("success"),
        ]

        second_result = analyzer.analyze(second_records)

        assert second_result["successes"] == 2
        assert second_result["failures"] == 0
        assert second_result["success_rate"] == 100.0