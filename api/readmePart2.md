# Part 2 – API Test Automation

## Overview

This module validates NASA's **Close-Approach Data (CAD) API** using an automated API testing framework built with **Python**, **Pytest**, and the **Requests** library.

The objective of this module is to verify that the API behaves correctly, returns well-formed data, and satisfies a set of functional and structural quality checks.

The API used:

https://ssd-api.jpl.nasa.gov/doc/cad.html

---

# Technology Stack

- Python 3.9+
- Pytest
- Requests
- Pytest HTML (Reporting)

---

# Project Structure

```
api/
│
├── api_client.py
├── response_validator.py
├── endpoints.py
├── constants.py
├── conftest.py
└── test_nasa_api.py
```

---

# Framework Design

The framework follows a modular architecture.

### ApiClient

Responsible for

- Sending HTTP Requests
- Building URLs
- Handling request configuration
- Returning Response objects

It contains **no assertions**.

---

### ResponseValidator

Responsible for

- Status Code validation
- JSON validation
- Schema validation
- Response time validation
- Content-Type validation
- Metadata validation

All assertions are centralized here.

---

### conftest.py

Common pytest fixtures.

Provides

- ApiClient instance
- ResponseValidator instance
- Common test data
- Query parameter fixtures

Using fixtures removes duplicate setup code and improves reusability.

---

### test_nasa_api.py

Contains all business test cases.

Tests focus only on

- Calling the API
- Validating business behaviour

They do not contain request-building logic.

---

# Definition of "Looks Sane"

The assignment leaves the definition of "looks sane" to the engineer.

For this implementation, the API response is considered sane when:

- HTTP Status Code is 200
- Response is valid JSON
- Mandatory keys are present
- Data array is not empty
- Response Content-Type is JSON
- Metadata (signature) exists
- Every data row matches the schema (fields array)

These validations avoid checking volatile data values that may legitimately change over time.

---

# Query Parameters Chosen

The following query parameters are used:

```
date-min
date-max
```

Example

```json
{
    "date-min": "2025-01-01",
    "date-max": "2025-01-31"
}
```

Reason

The assignment required at least one parameterized request.

A fixed date range was selected to validate query parameter handling while avoiding unnecessary assumptions about specific asteroid records.

---

# Test Cases

| Test ID | Description |
|----------|-------------|
| TC01 | Verify API returns HTTP 200 |
| TC02 | Verify response is valid JSON |
| TC03 | Verify mandatory response keys exist |
| TC04 | Verify data array is not empty |
| TC05 | Verify query parameters work correctly |
| TC06 | Verify invalid query parameter handling |
| TC07 | Verify response time |
| TC08 | Verify Content-Type |
| TC09 | Verify response schema consistency |
| TC10 | Verify signature metadata |

---

# Design Decisions

## Assertions

The framework intentionally avoids validating dynamic business values such as asteroid names or exact counts.

Instead, assertions focus on structural invariants such as:

- Response schema
- Required fields
- Data consistency
- Successful communication

This makes the tests stable and less likely to fail due to normal data changes.

---

## Why Fixtures?

Pytest fixtures are used to:

- Eliminate duplicate setup code
- Reuse ApiClient across tests
- Reuse ResponseValidator
- Share common query parameters

This improves maintainability and follows pytest best practices.

---

# Running Tests

Run all API tests

```bash
python -m pytest api/test_nasa_api.py -v
```

Run with console logs

```bash
python -m pytest api/test_nasa_api.py -v -s
```

Generate HTML report

```bash
python -m pytest api/test_nasa_api.py \
--html=reports/report.html \
--self-contained-html
```

---

# Expected Output

```
10 Passed
```

An HTML report is generated under

```
reports/report.html
```

---

# Future Improvements

Possible enhancements include:

- Request/Response logging
- Retry mechanism
- JSON Schema validation
- Authentication support
- API mocking
- Parallel execution
- CI/CD integration
- Docker execution

These were intentionally kept out of scope to keep the assignment focused on the requested functionality.