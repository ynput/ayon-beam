"""Test suite for cache_manager."""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ayon_beam.cache_manager.cache_client import CacheClient
    from ayon_beam.cache_manager.prefetcher import Prefetcher
    from pytest_ayon import ProjectInfo


# 


def test_prefetcher_get_assigned_tasks(project):
    """Test Prefetcher.get_assigned_tasks method."""
    from ayon_beam.cache_manager.prefetcher import Prefetcher

    user_name = "test_user"
    assigned_tasks = Prefetcher.get_assigned_tasks(user_name)

    assert isinstance(assigned_tasks, list)
    for task in assigned_tasks:
        assert "project_name" in task
        assert "folder_id" in task
        assert "task_id" in task