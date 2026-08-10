"""
Test Suite : NASA Close Approach Data API

This module contains automated API tests for NASA's
Close Approach Data API.

Test Cases
----------
TC01 - Verify API is reachable
TC02 - Verify response is JSON
TC03 - Verify mandatory keys exist
TC04 - Verify data is not empty
TC05 - Verify query parameters work
TC06 - Verify invalid query parameter
TC07 - Verify response time
TC08 - Verify Content-Type
TC09 - Verify field/data consistency
TC10 - Verify signature metadata
"""

import pytest


###############################################################
# TC01
###############################################################

def test_api_returns_success_status_code(api_client, validator):
    """
    Verify API returns HTTP 200.
    """

    response = api_client.get_close_approach_data()

    validator.validate_status_code(response)


###############################################################
# TC02
###############################################################

def test_response_is_valid_json(api_client, validator):
    """
    Verify response body is valid JSON.
    """

    response = api_client.get_close_approach_data()

    validator.validate_json(response)


###############################################################
# TC03
###############################################################

def test_response_contains_required_keys(api_client, validator):
    """
    Verify response contains:

    - signature
    - fields
    - data
    """

    response = api_client.get_close_approach_data()

    validator.validate_required_keys(response)


###############################################################
# TC04
###############################################################

def test_response_contains_non_empty_data(api_client, validator):
    """
    Verify data array is not empty.
    """

    response = api_client.get_close_approach_data()

    validator.validate_data_not_empty(response)


###############################################################
# TC05
###############################################################

def test_query_parameter_returns_filtered_data(
    api_client,
    validator,
    valid_date_range
):
    """
    Verify query parameters work.
    """

    response = api_client.get_close_approach_data(
        params=valid_date_range
    )

    validator.validate_status_code(response)
    validator.validate_json(response)
    validator.validate_required_keys(response)


###############################################################
# TC06
###############################################################

def test_invalid_query_parameter(
    api_client,
    invalid_date_range
):
    """
    Verify API behavior for invalid query.
    """

    response = api_client.get_close_approach_data(
        params=invalid_date_range
    )

    # API should never crash.
    assert response.status_code != 500


###############################################################
# TC07
###############################################################

def test_response_time(api_client, validator):
    """
    Verify response time is acceptable.
    """

    response = api_client.get_close_approach_data()

    validator.validate_response_time(
        response,
        max_time=5
    )


###############################################################
# TC08
###############################################################

def test_content_type(api_client, validator):
    """
    Verify response Content-Type.
    """

    response = api_client.get_close_approach_data()

    validator.validate_content_type(response)


###############################################################
# TC09
###############################################################

def test_fields_match_data_length(api_client, validator):
    """
    Every record should contain
    same number of values
    as the fields array.
    """

    response = api_client.get_close_approach_data()

    validator.validate_fields_and_data_length(response)


###############################################################
# TC10
###############################################################

def test_signature_metadata(api_client, validator):
    """
    Verify signature metadata.
    """

    response = api_client.get_close_approach_data()

    validator.validate_signature(response)