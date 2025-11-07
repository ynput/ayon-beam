"""AYON server connection context and API communication."""
from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Optional

import requests


class ServerConnection:
    """Connection context object for server communication."""

    def __init__(self, server_url: str, api_key: str):
        """Initialize connection to AYON server.

        Args:
            server_url: Server base URL
            api_key: Authentication token
        """
        self.base_url = server_url.rstrip("/")
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    def get(
            self, endpoint: str, **kwargs) -> requests.Response:  # noqa: ANN003
        """Make GET request to REST API endpoint.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments for `requests.get`_ method.
                params, headers, etc. See requests documentation for details.

        Returns:
            requests.Response: The response object from the GET request.

        .. _requests.get:
            https://docs.python-requests.org/en/latest/api/#requests.get

        """
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        return self.session.get(url, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make POST request to REST API endpoint."""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        return self.session.post(url, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make PUT request to REST API endpoint."""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        return self.session.put(url, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make DELETE request to REST API endpoint."""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        return self.session.delete(url, **kwargs)

    def graphql_query(
            self,
            query: str,
            variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query response data
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.post("graphql", json=payload)
        response.raise_for_status()
        return response.json()

    def get_server_info(self) -> dict[str, Any]:
        """Get server information.
        


        """
        response = self.get("/api/metrics")
        response.raise_for_status()
        return response.json()

    def is_connected(self) -> bool:
        """Check if the server connection is established.

        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            response = self.get("/api/info", timeout=5)

        except requests.RequestException:
            return False
        else:
            return response.ok
