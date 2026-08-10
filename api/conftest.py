"""
Common Pytest Fixtures

These fixtures are shared across all API test files.
"""

import pytest

from api.api_client import ApiClient
from api.response_validator import ResponseValidator


@pytest.fixture(scope="session")
def api_client():
    """
    Create one ApiClient object
    for the entire test session.
    """

    return ApiClient()


@pytest.fixture(scope="session")
def validator():
    """
    Create one ResponseValidator object
    for the entire test session.
    """

    return ResponseValidator()


@pytest.fixture
def valid_date_range():
    """
    Common query parameters
    used by multiple tests.
    """

    return {
        "date-min": "2025-01-01",
        "date-max": "2025-01-31"
    }


@pytest.fixture
def invalid_date_range():
    """
    Invalid query parameter.
    """

    return {
        "date-min": "INVALID_DATE"
    }