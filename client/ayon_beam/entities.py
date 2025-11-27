from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from arrow import Arrow

if TYPE_CHECKING:
    from ayon_beam.cache_manager import CacheManager
    from ..entities import Entity
    from .server import ServerContext


@dataclass
class Lifecycle:
    """Lifecycle information for an entity.

    Attributes:
        retrieved_at (Arrow): Timestamp when the entity was retrieved.
        from_cache (bool): Indicates if the entity was retrieved from cache.
        expired (bool): Indicates if the cached entity has expired.

    """
    retrieved_at: Arrow
    from_cache: bool
    expired: bool

    cache_manager: Optional[CacheManager] = field(
        init=False, default=None, repr=False
    )

    _entity_ref: Optional[Entity] = field(
        init=False, default=None, repr=False
    )

    def refetch(self) -> Optional[Entity]:
        """Refetch the data from the server to update the lifecycle.

        Returns:
            Updated entity instance
        """
        # Placeholder for actual refetch logic
        return self._entity_ref  # Replace with real refetch code



@dataclass
class Entity:
    """Base class for AYON entities."""
    Lifecycle: Lifecycle
    id: str = field(init=False, default="", repr=True)


@dataclass
class ProjectEntity(Entity):
    """Base class for AYON project-scoped entities."""
    project_name: str