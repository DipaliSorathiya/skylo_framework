import requests
from typing import Optional

from api.endpoints import BASE_URL, CLOSE_APPROACH_ENDPOINT
from api.constants import DEFAULT_TIMEOUT, DEFAULT_HEADERS


class ApiClient:
    """
    Reusable HTTP Client for NASA Close Approach API.

    Responsibilities:
        - Build complete URLs
        - Send HTTP requests
        - Handle common request configuration
        - Return Response object

    This class should NOT contain assertions.
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self.base_url = base_url
        self.timeout = timeout

    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> requests.Response:
        """
        Generic GET request.

        Args:
            endpoint: API endpoint path.
            params: Optional query parameters.
            headers: Optional request headers.

        Returns:
            requests.Response

        Raises:
            Exception: If timeout, connection, or request error occurs.
        """

        # Start with default headers
        final_headers = DEFAULT_HEADERS.copy()

        # Override/add custom headers
        if headers:
            final_headers.update(headers)

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(
                url=url,
                params=params,
                headers=final_headers,
                timeout=self.timeout
            )

            return response

        except requests.exceptions.Timeout:
            raise Exception(
                f"Request timed out after {self.timeout} seconds."
            )

        except requests.exceptions.ConnectionError:
            raise Exception(
                "Unable to connect to NASA API."
            )

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Request failed: {e}"
            )

    def get_close_approach_data(
        self,
        params: Optional[dict] = None
    ) -> requests.Response:
        """
        Calls NASA Close Approach Data API.

        Args:
            params: Optional query parameters.

        Returns:
            requests.Response
        """

        return self.get(
            endpoint=CLOSE_APPROACH_ENDPOINT,
            params=params
        )