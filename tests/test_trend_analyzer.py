from analyzer.models import Msg3Record
from analyzer.trend_analyzer import HourlyTrendAnalyzer


def create_record(
    timestamp,
    status
):
    return Msg3Record(
        timestamp=timestamp,
        rnti="100",
        message_type="MSG3",
        status=status
    )


class TestHourlyTrendAnalyzer:

    def test_single_hour_success_rate(self):

        records = [
            create_record(
                "2024-04-24 10:10:10",
                "success"
            ),
            create_record(
                "2024-04-24 10:20:10",
                "success"
            ),
            create_record(
                "2024-04-24 10:30:10",
                "failure"
            )
        ]

        result = HourlyTrendAnalyzer().analyze(
            records
        )

        assert len(
            result["hourly_trend"]
        ) == 1

        hour = result[
            "hourly_trend"
        ][0]

        assert hour["successes"] == 2
        assert hour["failures"] == 1
        assert hour["success_rate"] == 66.67

    def test_records_are_grouped_by_hour(self):

        records = [
            create_record(
                "2024-04-24 10:10:10",
                "success"
            ),
            create_record(
                "2024-04-24 10:50:10",
                "failure"
            ),
            create_record(
                "2024-04-24 11:10:10",
                "success"
            )
        ]

        result = HourlyTrendAnalyzer().analyze(
            records
        )

        assert len(
            result["hourly_trend"]
        ) == 2

        first_hour = result[
            "hourly_trend"
        ][0]

        assert first_hour["successes"] == 1
        assert first_hour["failures"] == 1
        assert first_hour["success_rate"] == 50.0

    def test_ignored_records_do_not_affect_trend(self):

        records = [
            create_record(
                "2024-04-24 10:10:10",
                "success"
            ),
            create_record(
                "2024-04-24 10:20:10",
                "unknown"
            ),
            create_record(
                "2024-04-24 10:30:10",
                "pending"
            )
        ]

        result = HourlyTrendAnalyzer().analyze(
            records
        )

        hour = result[
            "hourly_trend"
        ][0]

        assert hour["successes"] == 1
        assert hour["failures"] == 0
        assert hour["success_rate"] == 100.0

    def test_multiple_hours(self):

        records = [
            create_record(
                "2024-04-24 10:10:10",
                "success"
            ),
            create_record(
                "2024-04-24 10:20:10",
                "failure"
            ),
            create_record(
                "2024-04-24 11:10:10",
                "success"
            ),
            create_record(
                "2024-04-24 11:20:10",
                "success"
            )
        ]

        result = HourlyTrendAnalyzer().analyze(
            records
        )

        assert len(
            result["hourly_trend"]
        ) == 2

    def test_degradation_is_detected(self):

        records = []

        # 10:00 = 100%
        for _ in range(10):

            records.append(
                create_record(
                    "2024-04-24 10:10:10",
                    "success"
                )
            )

        # 11:00 = 70%
        for _ in range(7):

            records.append(
                create_record(
                    "2024-04-24 11:10:10",
                    "success"
                )
            )

        for _ in range(3):

            records.append(
                create_record(
                    "2024-04-24 11:20:10",
                    "failure"
                )
            )

        analyzer = HourlyTrendAnalyzer(
            degradation_threshold=10.0
        )

        result = analyzer.analyze(records)

        degradation = result[
            "degradation_windows"
        ]

        assert len(degradation) == 1

        assert (
            degradation[0][
                "previous_success_rate"
            ]
            == 100.0
        )

        assert (
            degradation[0][
                "current_success_rate"
            ]
            == 70.0
        )

        assert (
            degradation[0][
                "drop_percentage_points"
            ]
            == 30.0
        )

    def test_no_degradation_when_drop_is_below_threshold(self):

        records = []

        # 10:00 = 100%
        for _ in range(10):

            records.append(
                create_record(
                    "2024-04-24 10:10:10",
                    "success"
                )
            )

        # 11:00 = 95%
        for _ in range(19):

            records.append(
                create_record(
                    "2024-04-24 11:10:10",
                    "success"
                )
            )

        records.append(
            create_record(
                "2024-04-24 11:20:10",
                "failure"
            )
        )

        analyzer = HourlyTrendAnalyzer(
            degradation_threshold=10.0
        )

        result = analyzer.analyze(records)

        assert (
            result["degradation_windows"]
            == []
        )

    def test_invalid_degradation_threshold(self):

        try:

            HourlyTrendAnalyzer(
                degradation_threshold=-1
            )

            assert False

        except ValueError:
            assert True

    def test_invalid_timestamp_is_ignored(self):

        records = [
            create_record(
                "INVALID_TIMESTAMP",
                "success"
            )
        ]

        result = HourlyTrendAnalyzer().analyze(
            records
        )

        assert (
            result["hourly_trend"]
            == []
        )