"""
Reusable Response Validation Library

This class contains common assertions that can be reused
across multiple API test cases.

Responsibilities
----------------
1. Validate HTTP Status Code
2. Validate JSON Response
3. Validate Mandatory Keys
4. Validate Response Time
5. Validate Data Integrity
6. Validate Content-Type
"""

from requests import Response


class ResponseValidator:

    @staticmethod
    def validate_status_code(
            response: Response,
            expected_status: int = 200
    ):
        """
        Validate HTTP Status Code.
        """

        assert response.status_code == expected_status, (
            f"Expected Status Code {expected_status}, "
            f"but received {response.status_code}"
        )

    @staticmethod
    def validate_content_type(response: Response):
        """
        Validate response is JSON.
        """

        content_type = response.headers.get("Content-Type", "")

        assert "application/json" in content_type, (
            f"Unexpected Content-Type : {content_type}"
        )

    @staticmethod
    def validate_json(response: Response):
        """
        Ensure response body is valid JSON.
        """

        try:
            response.json()
        except ValueError:
            raise AssertionError("Response is not a valid JSON")

    @staticmethod
    def validate_required_keys(response: Response):

        """
        Validate Mandatory Keys.

        NASA API should contain

        signature
        fields
        data
        """

        body = response.json()

        required_keys = [
            "signature",
            "fields",
            "data"
        ]

        for key in required_keys:

            assert key in body, (
                f"Missing key : {key}"
            )

    @staticmethod
    def validate_data_not_empty(response: Response):

        body = response.json()

        assert len(body["data"]) > 0, (
            "Returned data is empty."
        )

    @staticmethod
    def validate_response_time(
            response: Response,
            max_time: float = 5.0
    ):
        """
        Validate API Response Time.

        Default : 5 Seconds
        """

        response_time = response.elapsed.total_seconds()

        assert response_time < max_time, (
            f"Response Time {response_time}s "
            f"is greater than {max_time}s"
        )

    @staticmethod
    def validate_fields_and_data_length(response: Response):

        """
        Every record should contain
        same number of values
        as field names.
        """

        body = response.json()

        fields = body["fields"]

        data = body["data"]

        for row in data:

            assert len(row) == len(fields), (
                "Field count mismatch."
            )

    @staticmethod
    def validate_signature(response: Response):

        body = response.json()

        assert body["signature"] is not None

        assert "version" in body["signature"]

        assert "source" in body["signature"]