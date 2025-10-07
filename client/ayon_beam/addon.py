"""AYON Beam addon - Smart caching and entity-centric API."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

from ayon_core.addon import AYONAddon, IPluginPaths, ITrayService

from .cache_manager import CacheService, CacheServiceConfig, RateLimitConfig

logger = logging.getLogger(__name__)


class BeamAddon(AYONAddon, IPluginPaths, ITrayService):
    """Beam addon for AYON - Smart caching and entity-centric API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_service: Optional[CacheService] = None
        self._cache_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def name(self):
        return "ayon-beam"

    @property
    def label(self) -> str:
        return "AYON Beam Caching Server"

    def initialize(self, settings: dict[str, Any]):
        """Initialize the addon with settings."""
        # This could be called during addon initialization

    def tray_init(self) -> None:
        """Initialize the tray service."""
        logger.info("Initializing Beam addon tray service")

        try:
            # Create event loop for async operations
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Get configuration from environment or settings
            config = self._get_cache_config()

            if config:
                # Initialize cache service
                self._cache_service = CacheService(config)
                logger.info("Cache service initialized")
            else:
                logger.warning("Cache service not configured - missing required settings")

        except Exception as e:
            logger.error("Failed to initialize Beam addon: %s", e)

    def tray_start(self) -> None:
        """Start the tray service."""
        logger.info("Starting Beam addon tray service")

        if not self._cache_service or not self._loop:
            logger.error("Cache service not initialized")
            return

        try:
            # Start cache service in background task
            self._cache_task = self._loop.create_task(self._run_cache_service())

            # Run the event loop in a separate thread to avoid blocking
            import threading

            def run_loop():
                self._loop.run_forever()

            self._loop_thread = threading.Thread(target=run_loop, daemon=True)
            self._loop_thread.start()

            logger.info("AYON Beam addon started successfully")

        except Exception as e:
            logger.error("Failed to start Beam addon: %s", e)

    def tray_exit(self) -> None:
        """Stop the tray service."""
        logger.info("Stopping AYON Beam addon tray service")

        try:
            if self._cache_service:
                # Schedule the stop coroutine
                if self._loop and not self._loop.is_closed():
                    future = asyncio.run_coroutine_threadsafe(
                        self._cache_service.stop(),
                        self._loop
                    )
                    future.result(timeout=10)  # Wait up to 10 seconds

            # Stop the event loop
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)

            logger.info("Beam addon stopped")

        except Exception as e:
            logger.error("Error stopping Beam addon: %s", e)

    async def _run_cache_service(self):
        """Run the cache service."""
        try:
            await self._cache_service.start()
            # Keep running until stopped
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Cache service task cancelled")
        except Exception as e:
            logger.error("Cache service error: %s", e)

    def _get_cache_config(self) -> Optional[CacheServiceConfig]:
        """Get cache service configuration from environment and settings.

        Returns:
            Cache configuration or None if not properly configured
        """
        try:
            # Get server connection info from environment
            server_url = os.getenv("AYON_SERVER_URL")
            api_key = os.getenv("AYON_API_KEY")

            if not server_url or not api_key:
                logger.error("Missing AYON_SERVER_URL or AYON_API_KEY environment variables")
                return None

            # Get memcached settings from environment
            memcache_host = os.getenv("BEAM_MEMCACHE_HOST", "localhost")
            memcache_port = int(os.getenv("BEAM_MEMCACHE_PORT", "11211"))

            # Get rate limiting settings
            rate_limit_config = RateLimitConfig(
                requests_per_second=float(os.getenv("BEAM_RATE_LIMIT_RPS", "5.0")),
                burst_limit=int(os.getenv("BEAM_BURST_LIMIT", "10")),
                cooldown_period=float(os.getenv("BEAM_COOLDOWN_PERIOD", "60.0")),
                per_project_limit=float(os.getenv("BEAM_PROJECT_RATE_LIMIT", "2.0"))
            )

            # Get caching settings
            default_ttl = int(os.getenv("BEAM_DEFAULT_TTL", "3600"))
            prefetch_interval = int(os.getenv("BEAM_PREFETCH_INTERVAL", "300"))
            max_concurrent_fetches = int(os.getenv("BEAM_MAX_CONCURRENT", "5"))

            # Get projects and folders to cache from environment
            projects_to_cache = []
            folders_to_cache = {}

            # Example: BEAM_PROJECTS="TestProject,AnotherProject"
            projects_env = os.getenv("BEAM_PROJECTS", "")
            if projects_env:
                projects_to_cache = [p.strip() for p in projects_env.split(",") if p.strip()]

            # Example: BEAM_FOLDERS_TestProject="folder1,folder2"
            for project in projects_to_cache:
                folders_env = os.getenv(f"BEAM_FOLDERS_{project}", "")
                if folders_env:
                    folders_to_cache[project] = [f.strip() for f in folders_env.split(",") if f.strip()]

            config = CacheServiceConfig(
                server_url=server_url,
                api_key=api_key,
                memcache_host=memcache_host,
                memcache_port=memcache_port,
                default_ttl=default_ttl,
                rate_limit_config=rate_limit_config,
                prefetch_interval=prefetch_interval,
                max_concurrent_fetches=max_concurrent_fetches,
                projects_to_cache=projects_to_cache,
                folders_to_cache=folders_to_cache
            )

            logger.info(f"Cache config created for {len(projects_to_cache)} projects")
            return config

        except Exception as e:
            logger.error("Failed to create cache configuration: %s", e)
            return None

    def get_cache_service(self) -> Optional[CacheService]:
        """Get the cache service instance.

        Returns:
            Cache service instance or None if not available
        """
        return self._cache_service

    async def get_folder_data(
            self, project_name: str,
            folder_id: str,
            force_refresh: bool = False) -> Optional[dict[str, Any]]:
        """Get folder data through the cache service.

        Args:
            project_name: Name of the project
            folder_id: ID of the folder
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Folder data with products and tasks
        """
        if not self._cache_service:
            logger.error("Cache service not available")
            return None

        return await self._cache_service.get_folder_data(
            project_name, folder_id, force_refresh)

    def get_service_stats(self) -> dict[str, Any]:
        """Get comprehensive service statistics.

        Returns:
            Dictionary with service statistics
        """
        if not self._cache_service:
            return {"error": "Cache service not available"}

        return self._cache_service.get_service_stats()

    def add_project_to_cache(self, project_name: str, folder_ids: list):
        """Add a project and its folders to the caching list.

        Args:
            project_name: Name of the project
            folder_ids: List of folder IDs to cache
        """
        if self._cache_service:
            self._cache_service.add_project_to_cache(project_name, folder_ids)
        else:
            logger.error("Cache service not available")

    def remove_project_from_cache(self, project_name: str):
        """Remove a project from the caching list.

        Args:
            project_name: Name of the project to remove
        """
        if self._cache_service:
            self._cache_service.remove_project_from_cache(project_name)
        else:
            logger.error("Cache service not available")

    def update_cache_configuration(
            self, projects_config: dict[str, list[str]]):
        """Dynamically update the projects and folders to cache.

        Args:
            projects_config: Dictionary mapping project names to lists of folder IDs
        """
        if self._cache_service:
            self._cache_service.update_cache_configuration(projects_config)
        else:
            logger.error("Cache service not available")

    def get_cache_configuration(self) -> dict[str, list[str]]:
        """Get current cache configuration.

        Returns:
            Dictionary mapping project names to folder IDs
        """
        if self._cache_service:
            return self._cache_service.get_cache_configuration()
        logger.error("Cache service not available")
        return {}

    def add_folders_to_project(self, project_name: str, folder_ids: list[str], replace: bool = False):
        """Add or update folders for a specific project.

        Args:
            project_name: Name of the project
            folder_ids: List of folder IDs to add/set
            replace: If True, replace existing folders; if False, merge with existing
        """
        if self._cache_service:
            self._cache_service.add_folders_to_project(project_name, folder_ids, replace)
        else:
            logger.error("Cache service not available")

    def remove_folders_from_project(self, project_name: str, folder_ids: list[str] = None):
        """Remove specific folders or entire project from caching.

        Args:
            project_name: Name of the project
            folder_ids: Specific folder IDs to remove. If None, removes entire project.
        """
        if self._cache_service:
            self._cache_service.remove_folders_from_project(
                project_name, folder_ids)
        else:
            logger.error("Cache service not available")

    async def trigger_immediate_prefetch(
            self, project_name: Optional[str] = None,
            folder_ids: Optional[list[str]] = None):
        """Trigger immediate prefetch for specific projects/folders.

        Args:
            project_name: Specific project to prefetch.
                If None, prefetch all configured.
            folder_ids: Specific folder IDs to prefetch.
                If None, prefetch all in project.
        """
        if self._cache_service:
            if self._loop and not self._loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(
                    self._cache_service.trigger_immediate_prefetch(
                        project_name, folder_ids),
                    self._loop
                )
                try:
                    future.result(timeout=30)
                except Exception as e:
                    logger.error("Failed to trigger prefetch: %s", e)
        else:
            logger.error("Cache service not available")

    def get_project_folders(self, project_name: str) -> list[str]:
        """Get configured folder IDs for a specific project.

        Args:
            project_name: Name of the project

        Returns:
            List of folder IDs configured for the project
        """
        if self._cache_service:
            return self._cache_service.get_project_folders(project_name)
        logger.error("Cache service not available")
        return []
