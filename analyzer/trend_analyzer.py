from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from analyzer.models import Msg3Record
from analyzer.constants import (
    SUCCESS_STATUS,
    FAILURE_STATUS,
)


DEFAULT_DEGRADATION_THRESHOLD = 10.0


class HourlyTrendAnalyzer:
    """
    Part 1 Bonus:

    1. Calculates MSG3 success rate per hour.
    2. Detects significant degradation between
       consecutive hourly buckets.

    Existing Part 1 analyzer is not modified.
    """

    def __init__(
        self,
        degradation_threshold: float = DEFAULT_DEGRADATION_THRESHOLD
    ):
        if degradation_threshold < 0:
            raise ValueError(
                "Degradation threshold cannot be negative."
            )

        self.degradation_threshold = degradation_threshold

    def analyze(
        self,
        records: List[Msg3Record]
    ) -> Dict:
        """
        Analyze MSG3 records by hour.

        Ignored/unrecognized statuses are excluded.

        Returns:
            {
                "degradation_threshold": 10.0,
                "hourly_trend": [...],
                "degradation_windows": [...]
            }
        """

        hourly_records = defaultdict(list)

        # --------------------------------------------------
        # 1. Group measurable records by hour
        # --------------------------------------------------

        for record in records:

            if not record.timestamp:
                continue

            status = record.status.strip().lower()

            # Only measurable statuses participate
            # in hourly success-rate calculation.
            if (
                status not in SUCCESS_STATUS
                and status not in FAILURE_STATUS
            ):
                continue

            timestamp = self._parse_timestamp(
                record.timestamp
            )

            # Malformed timestamp:
            # safely ignore instead of crashing.
            if timestamp is None:
                continue

            hour_bucket = timestamp.replace(
                minute=0,
                second=0,
                microsecond=0
            )

            hourly_records[hour_bucket].append(
                record
            )

        # --------------------------------------------------
        # 2. Calculate hourly statistics
        # --------------------------------------------------

        hourly_trend = []

        for hour in sorted(hourly_records):

            successes = 0
            failures = 0

            for record in hourly_records[hour]:

                status = record.status.strip().lower()

                if status in SUCCESS_STATUS:
                    successes += 1

                elif status in FAILURE_STATUS:
                    failures += 1

            measurable = successes + failures

            if measurable == 0:
                success_rate = None
            else:
                success_rate = (
                    successes / measurable
                ) * 100

            hourly_trend.append(
                {
                    "hour": hour.strftime(
                        "%Y-%m-%d %H:00:00"
                    ),
                    "successes": successes,
                    "failures": failures,
                    "success_rate": (
                        round(success_rate, 2)
                        if success_rate is not None
                        else None
                    )
                }
            )

        # --------------------------------------------------
        # 3. Detect degradation
        # --------------------------------------------------

        degradation_windows = (
            self._detect_degradation(
                hourly_trend
            )
        )

        return {
            "degradation_threshold": (
                self.degradation_threshold
            ),
            "hourly_trend": hourly_trend,
            "degradation_windows": (
                degradation_windows
            )
        }

    @staticmethod
    def _parse_timestamp(
        timestamp: str
    ) -> Optional[datetime]:
        """
        Convert the existing parser timestamp string
        into datetime.

        This does NOT change Msg3Record.timestamp.

        Supported formats:
            YYYY-MM-DD HH:MM:SS
            YYYY-MM-DD HH:MM
            YYYY-MM-DD
        """

        timestamp = timestamp.strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]

        for timestamp_format in formats:

            try:
                return datetime.strptime(
                    timestamp,
                    timestamp_format
                )

            except ValueError:
                continue

        return None

    def _detect_degradation(
        self,
        hourly_trend: List[Dict]
    ) -> List[Dict]:
        """
        Detect a significant drop between
        consecutive hourly success rates.

        Example:

            Previous = 98%
            Current  = 80%

            Drop = 18 percentage points

            Threshold = 10

            18 >= 10
            => degradation detected
        """

        degradation_windows = []

        for index in range(
            1,
            len(hourly_trend)
        ):

            previous = hourly_trend[
                index - 1
            ]

            current = hourly_trend[
                index
            ]

            previous_rate = previous[
                "success_rate"
            ]

            current_rate = current[
                "success_rate"
            ]

            # Cannot calculate degradation when
            # either hour has no measurable data.
            if (
                previous_rate is None
                or current_rate is None
            ):
                continue

            drop = (
                previous_rate
                - current_rate
            )

            if drop >= self.degradation_threshold:

                degradation_windows.append(
                    {
                        "from_hour": previous[
                            "hour"
                        ],
                        "to_hour": current[
                            "hour"
                        ],
                        "previous_success_rate": (
                            previous_rate
                        ),
                        "current_success_rate": (
                            current_rate
                        ),
                        "drop_percentage_points": (
                            round(drop, 2)
                        )
                    }
                )

        return degradation_windows