"""Project and related API interactions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from arrow import Arrow

    from .project_anatomy import ProjectAnatomy
    from .server import ServerContext


@dataclass
class AttributeDefinition:
    """Definition of a custom attribute in a project."""

    name: str
    type: str
    is_required: bool


@dataclass
class Project:
    """Represents a project in the Ayon system.

    Attributes:
        name: The name of the project.
        code: The unique code identifier for the project.
        active: Whether the project is active.
        library: Whether the project is a library project.
        created_at: Timestamp of project creation.
        updated_at: Timestamp of last project update.

        attributes: Custom attributes defined for the project.
    """

    name: str
    code: str
    active: bool
    library: bool
    created_at: Arrow
    updated_at: Arrow
    attributes: Optional[dict[str, Any]] = None
    data: Optional[dict[str, Any]] = None
    own_attributes: Optional[list[str]] = None
    connection: Optional[ServerContext] = None

    _anatomy: Optional[ProjectAnatomy] = field(
        init=False, default=None, repr=False
    )

    @property
    def anatomy(self) -> Optional[ProjectAnatomy]:
        """Lazily load and return the project's anatomy schema.

        Returns:
            Optional[ProjectAnatomy]: The project's anatomy
                schema if available.
        """
        if self._anatomy is None:
            # Placeholder for actual anatomy loading logic
            self._anatomy = None  # Replace with real loading code
        return self._anatomy

    def to_dict(self) -> dict[str, Any]:
        """Convert the Project instance to a dictionary.

        Returns:
            Dict[str, Any]: The project represented as a dictionary.
        """
        return {
            "name": self.name,
            "attributes": self.attributes or {},
        }
