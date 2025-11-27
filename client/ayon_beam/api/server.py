from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


from .project import Project

from ..entities import Entity
from ..connection import ServerConnection

@dataclass
class ReleaseInfo(Entity):
    """Release information of the AYON server.

    Attributes:
        version: Server version string.
        build_date: Build date of the server.
        uptime: Uptime duration string.

    """
    version: str
    build_date: str
    build_time: str
    frontend_branch: str
    backend_branch: str
    frontend_commit: str
    backend_commit: str

@dataclass
class ServerInfo(Entity):
    """Information about the AYON server.

    Attributes:
        version: Server version string.
        build_date: Build date of the server.
        uptime: Uptime duration string.
        additional_info: Any additional server information.

    """
    motd: str
    login_page_background: str  # url to background image
    login_page_brand: str  # url to brand image
    release_info: ReleaseInfo
    version: str
    uptime: int
    no_admin_user: bool
    onboarding: bool
    disable_changelog: bool
    hide_password_auth: bool
    password_recovery_available: bool


@dataclass
class ServerContext(Entity):
    """Context for AYON server communication.

    Attributes:
        connection (ServerConnection): The server connection instance.
        project_name (Optional[str]): The name of the project in context.

    """
    connection: Optional[ServerConnection] = None

    def is_connected(self) -> bool:
        """Check if the server connection is established.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.connection is not None and self.connection.is_connected()

    def get_project(self, project_name: str) -> Project:
        """Fetch project details from the server.

        Args:
            project_name (str): The name of the project to fetch.

        Returns:
            Project: The fetched project instance.

        Raises:
            RuntimeError: If not connected to the server.

        """
        if not self.is_connected() or self.connection is None:
            msg = "Not connected to the server."
            raise RuntimeError(msg)

        response = self.connection.get(f"/api/projects/{project_name}")
        response.raise_for_status()
        project_data = response.json()

        return Project(
            name=project_data["name"],
            code=project_data["code"],
            active=project_data["active"],
            library=project_data["library"],
            created_at=project_data["created_at"],
            updated_at=project_data["updated_at"],
            connection=self.connection
        )
