import pytest

from analyzer.models import Msg3Record
from gate.quality_gate import QualityGate


def create_record(status):
    """
    Helper method to create a Msg3Record
    for quality-gate unit tests.
    """

    return Msg3Record(
        timestamp="2024-01-01 10:00:00",
        rnti="100",
        message_type="MSG3-RRC-C-REQ",
        status=status
    )


class TestQualityGate:

    # ============================================================
    # TC01 - Gate passes above threshold
    # ============================================================

    def test_gate_passes_above_threshold(self):

        records = [
            create_record("success"),
            create_record("success"),
            create_record("success"),
            create_record("failure")
        ]

        gate = QualityGate(
            minimum_success_rate=75.0
        )

        result = gate.evaluate(records)

        assert result["success_rate"] == 75.0
        assert result["success_threshold"] == 75.0
        assert result["gate_status"] == "PASS"
        assert result["gate_passed"] is True

    # ============================================================
    # TC02 - Gate fails below threshold
    # ============================================================

    def test_gate_fails_below_threshold(self):

        records = [
            create_record("success"),
            create_record("failure")
        ]

        gate = QualityGate(
            minimum_success_rate=95.0
        )

        result = gate.evaluate(records)

        assert result["success_rate"] == 50.0
        assert result["success_threshold"] == 95.0
        assert result["gate_status"] == "FAIL"
        assert result["gate_passed"] is False

    # ============================================================
    # TC03 - Exact threshold passes
    # ============================================================

    def test_gate_passes_at_exact_threshold(self):

        records = [
            create_record("success")
            for _ in range(19)
        ]

        records.append(
            create_record("failure")
        )

        gate = QualityGate(
            minimum_success_rate=95.0
        )

        result = gate.evaluate(records)

        assert result["success_rate"] == 95.0
        assert result["success_threshold"] == 95.0
        assert result["gate_status"] == "PASS"
        assert result["gate_passed"] is True

    # ============================================================
    # TC04 - Ignored records do not affect gate
    # ============================================================

    def test_ignored_records_do_not_affect_gate(self):

        records = [
            create_record("success"),
            create_record("success"),
            create_record("failure"),
            create_record("unknown"),
            create_record("pending"),
            create_record("ignored")
        ]

        gate = QualityGate(
            minimum_success_rate=66.67
        )

        result = gate.evaluate(records)

        assert result["successes"] == 2
        assert result["failures"] == 1
        assert result["ignored"] == 3

        assert result["success_rate"] == pytest.approx(
            66.67,
            abs=0.01
        )

        assert result["success_threshold"] == 66.67
        assert result["gate_status"] == "PASS"
        assert result["gate_passed"] is True

    # ============================================================
    # TC05 - Empty records
    # ============================================================

    def test_empty_records(self):

        gate = QualityGate(
            minimum_success_rate=95.0
        )

        result = gate.evaluate([])

        assert result["successes"] == 0
        assert result["failures"] == 0
        assert result["ignored"] == 0

        # No measurable records means the success rate
        # is mathematically undefined.
        assert result["success_rate"] is None

        # Undefined success rate must fail the quality gate.
        assert result["success_threshold"] == 95.0
        assert result["gate_status"] == "FAIL"
        assert result["gate_passed"] is False

    # ============================================================
    # TC06 - Invalid threshold below zero
    # ============================================================

    def test_invalid_threshold_below_zero(self):

        with pytest.raises(ValueError):

            QualityGate(
                minimum_success_rate=-1
            )

    # ============================================================
    # TC07 - Invalid threshold above 100
    # ============================================================

    def test_invalid_threshold_above_100(self):

        with pytest.raises(ValueError):

            QualityGate(
                minimum_success_rate=101
            )

    # ============================================================
    # TC08 - Failure statuses are counted
    # ============================================================

    def test_failure_statuses_are_counted(self):

        records = [
            create_record("success"),
            create_record("timeout"),
            create_record("failed"),
            create_record("rejected")
        ]

        gate = QualityGate(
            minimum_success_rate=50.0
        )

        result = gate.evaluate(records)

        assert result["successes"] == 1
        assert result["failures"] == 3
        assert result["ignored"] == 0

        assert result["success_rate"] == 25.0
        assert result["success_threshold"] == 50.0
        assert result["gate_status"] == "FAIL"
        assert result["gate_passed"] is False
