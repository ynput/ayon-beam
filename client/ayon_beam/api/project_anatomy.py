"""Data classes representing the project anatomy schema.

TODO (antirotor): Add docstrings to all classes and fields.
    Add better types where possible - like RGB hex codes, etc.
    Connect anatomy templates to Anatomy object?

"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EntityNaming:
    """Naming conventions for entities in the project anatomy.

    Capitalization options could be 'camelCase', 'PascalCase', 'lower', etc.
    Separator options could be '_', '-', or '' (no separator) or others.

    """
    capitalization: str
    separator: str


@dataclass
class Root:
    """Project root directory structure.

    Represents the root paths for different operating systems.

    """
    name: str
    windows: str
    linux: str
    darwin: str


@dataclass
class Template:
    """Template structure for various project elements.

    This kind of template typically includes a directory and an optional file.

    """
    name: str
    directory: str
    file: Optional[str] = None


@dataclass
class StagingTemplate:
    """Staging template structure."""
    name: str
    directory: str


@dataclass
class OtherTemplate:
    """Other template structure.

    Custom templates that do not fit into other categories.

    """
    name: str
    value: str


@dataclass
class Templates:
    """Templates for different project elements."""
    version_padding: int
    version: str
    frame_padding: int
    frame: str
    work: list[Template]
    publish: list[Template]
    hero: list[Template]
    delivery: list[Template]
    staging: list[StagingTemplate]
    others: list[OtherTemplate]


@dataclass
class FolderType:
    """Folder type definition."""
    name: str
    short_name: str
    icon: str


@dataclass
class TaskType:
    """Task type definition."""
    name: str
    short_name: str
    color: str
    icon: str


@dataclass
class LinkType:
    """Link type definition."""
    link_type: str
    input_type: str
    output_type: str
    color: str  # rgb hex code
    style: str  # solid, dashed, dotted


@dataclass
class Status:
    """Status definition."""
    name: str
    short_name: str
    state: str
    icon: str
    color: str
    scope: list[str]


@dataclass
class Tag:
    """Tag definition."""
    name: str
    color: str


@dataclass
class ProductBaseTypeDefinition:
    """Product base type definition."""
    name: str
    color: str
    icon: str


@dataclass
class ProductBaseTypes:
    """Product base types definition."""
    default: dict[str, str]
    definitions: list[ProductBaseTypeDefinition]


@dataclass
class ProjectAnatomy:
    """Comprehensive project anatomy schema."""
    entity_naming: EntityNaming
    roots: list[Root]
    templates: Templates
    folder_types: list[FolderType]
    task_types: list[TaskType]
    link_types: list[LinkType]
    statuses: list[Status]
    tags: list[Tag]
    product_base_types: ProductBaseTypes
