"""Tests to run in local environment."""
from loguru import logger
PROJECT_NAME = "TestProject"


def test_prefetcher_get_assigned_tasks(project):
    """Test Prefetcher.get_assigned_tasks method."""
    from ayon_beam.cache_manager.prefetcher import Prefetcher

    user_name = "antirotor"
    assigned_tasks = Prefetcher.get_assigned_tasks(user_name)

    for task in assigned_tasks:
        logger.debug(task)
