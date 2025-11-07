"""GraphQL client for fetching data from AYON server."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import aiohttp
from loguru import logger

if TYPE_CHECKING:
    from types import TracebackType


@dataclass
class GraphQLQuery:
    """GraphQL query configuration."""
    project_name: str
    folder_id: str

    @staticmethod
    def build_query() -> str:
        """Build the GraphQL query string.

        Returns:
            GraphQL query string

        """
        return """
query FetchData($projectName: String!, $folderId: String!) {
    project(name: $projectName) {
    folder(id: $folderId) {
        id
        name
        path
        folderType
        products {
            edges {
            node {
                id
                productType
                productBaseType
                path
                name
                data
                active
                type
                tags
                status
            }
            }
        }
        tasks {
            edges {
            node {
                id
                label
                name
                path
                status
                tags
                taskType
                updatedAt
                active
                allAttrib
                assignees
                createdAt
                data
                versions {
                edges {
                    node {
                    allAttrib
                    active
                    data
                    author
                    createdAt
                    id
                    name
                    parents
                    path
                    version
                    updatedAt
                    tags
                    status
                    productId
                    product {
                        productType
                        projectName
                        updatedAt
                        data
                        active
                    }
                    }
                }
                }
            }
            }
        }
        allAttrib
        }
        allAttrib
    }
    }
        """

    def get_variables(self) -> dict[str, str]:
        """Get query variables.

        Returns:
            Dictionary of query variables

        """
        return {
            "projectName": self.project_name,
            "folderId": self.folder_id
        }


class GraphQLClient:
    """Async GraphQL client for AYON server."""

    def __init__(self, server_url: str, api_key: str):
        """Initialize GraphQL client.

        Args:
            server_url: AYON server URL
            api_key: API key for authentication
        """
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.graphql_endpoint = f"{self.server_url}/graphql"
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry.

        Returns:
            GraphQLClient instance

        """
        await self.start()
        return self

    async def __aexit__(
            self,
            exc_type: Optional[type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the HTTP session."""
        if self._session is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )

    async def close(self)  -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def execute_query(
            self, query: GraphQLQuery) -> Optional[dict[str, Any]]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query to execute

        Returns:
            Query response data or None if failed

        """
        if not self._session:
            await self.start()

        payload = {
            "query": query.build_query(),
            "variables": query.get_variables()
        }

        if  not self._session:
            logger.error("HTTP session is not initialized")
            return None

        try:
            async with self._session.post(
                self.graphql_endpoint,
                json=payload
            ) as response:
                if response.ok:
                    result = await response.json()
                    if "errors" in result:
                        logger.error(f"GraphQL errors: {result['errors']}")
                        return None
                    return result.get("data")
                logger.error(f"HTTP error {response.status}: "
                                f"{await response.text()}")
                return None

        except Exception as e:  # noqa: BLE001
            logger.exception(f"GraphQL query failed: {e}")
            return None

    async def fetch_folder_data(
            self,
            project_name: str, folder_id: str) -> Optional[dict[str, Any]]:
        """Fetch data for a specific folder.

        Args:
            project_name: Name of the project
            folder_id: ID of the folder

        Returns:
            Folder data with products and tasks
        """
        query = GraphQLQuery(project_name, folder_id)
        data = await self.execute_query(query)

        if data and "project" in data and data["project"]:
            return data["project"]["folder"]

        return None
