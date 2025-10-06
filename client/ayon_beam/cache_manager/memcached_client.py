"""Memcached client for caching AYON hierarchy data."""

import logging
from typing import Any, Optional
from datetime import datetime
from pymemcache.client.base import Client
from pymemcache import serde
import hashlib


logger = logging.getLogger(__name__)


class MemcachedClient:
    """Wrapper for pymemcache with AYON-specific caching logic."""

    def __init__(self, host: str = 'localhost', port: int = 11211):
        """Initialize memcached client.

        Args:
            host: Memcached server host
            port: Memcached server port
        """
        self.host = host
        self.port = port
        self._client = None
        self._key_tracker: set[str] = set()  # Track keys for invalidation

    def connect(self):
        """Connect to memcached server."""
        try:
            self._client = Client(
                (self.host, self.port),
                serde=serde.CompressedSerde,
                connect_timeout=5.0,
                timeout=10.0
            )
            # Test connection
            self._client.version()
            logger.info(f"Connected to memcached at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to memcached: {e}")
            raise

    def disconnect(self):
        """Disconnect from memcached server."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Disconnected from memcached")

    def _generate_key(self, project_name: str, folder_id: str, data_type: str = "folder") -> str:
        """Generate a cache key for the data.

        Args:
            project_name: Name of the project
            folder_id: ID of the folder
            data_type: Type of data (folder, products, tasks)

        Returns:
            Cache key string
        """
        key_base = f"ayon:{project_name}:{folder_id}:{data_type}"
        # Use hash for consistent key length
        key_hash = hashlib.md5(key_base.encode()).hexdigest()
        return f"ayon_{key_hash}"

    def _generate_metadata_key(self, cache_key: str) -> str:
        """Generate metadata key for cache entry."""
        return f"{cache_key}_meta"

    def store_folder_data(
            self,
            project_name: str,
            folder_id: str, data: dict[str, Any], ttl: int = 3600) -> bool:
        """Store folder data in cache.

        Args:
            project_name: Name of the project
            folder_id: ID of the folder
            data: Folder data to store
            ttl: Time to live in seconds

        Returns:
            True if stored successfully, False otherwise
        """
        if not self._client:
            logger.error("Not connected to memcached")
            return False

        try:
            cache_key = self._generate_key(project_name, folder_id, "folder")
            metadata_key = self._generate_metadata_key(cache_key)

            # Store main data
            success = self._client.set(cache_key, data, expire=ttl)

            if success:
                # Store metadata for tracking
                metadata = {
                    "project_name": project_name,
                    "folder_id": folder_id,
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl": ttl,
                    "data_type": "folder"
                }
                self._client.set(metadata_key, metadata, expire=ttl + 300)  # Keep metadata a bit longer

                # Track key for invalidation
                self._key_tracker.add(cache_key)

                logger.debug(f"Stored folder data for {project_name}:{folder_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to store folder data: {e}")

        return False

    def get_folder_data(
            self,
            project_name: str, folder_id: str) -> Optional[dict[str, Any]]:
        """Retrieve folder data from cache.

        Args:
            project_name: Name of the project
            folder_id: ID of the folder

        Returns:
            Cached folder data or None if not found
        """
        if not self._client:
            logger.error("Not connected to memcached")
            return None

        try:
            cache_key = self._generate_key(project_name, folder_id, "folder")
            data = self._client.get(cache_key)

            if data:
                logger.debug(f"Retrieved folder data for {project_name}:{folder_id}")
                return data
            else:
                logger.debug(f"No cached data found for {project_name}:{folder_id}")

        except Exception as e:
            logger.error(f"Failed to retrieve folder data: {e}")

        return None

    def invalidate_folder(self, project_name: str, folder_id: str) -> bool:
        """Invalidate cached data for a specific folder.

        Args:
            project_name: Name of the project
            folder_id: ID of the folder

        Returns:
            True if invalidated successfully
        """
        if not self._client:
            logger.error("Not connected to memcached")
            return False

        try:
            cache_key = self._generate_key(project_name, folder_id, "folder")
            metadata_key = self._generate_metadata_key(cache_key)

            # Delete both data and metadata
            self._client.delete(cache_key)
            self._client.delete(metadata_key)

            # Remove from tracker
            self._key_tracker.discard(cache_key)

            logger.info(f"Invalidated cache for {project_name}:{folder_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate folder cache: {e}")
            return False

    def invalidate_project(self, project_name: str) -> int:
        """Invalidate all cached data for a project.

        Args:
            project_name: Name of the project

        Returns:
            Number of keys invalidated
        """
        if not self._client:
            logger.error("Not connected to memcached")
            return 0

        invalidated_count = 0

        # We need to track keys better for project-level invalidation
        # For now, we'll use a simple pattern matching approach
        try:
            # This is a simplified approach - in production you'd want
            # a more sophisticated key tracking system
            keys_to_remove = []
            for key in self._key_tracker.copy():
                # Get metadata to check project
                metadata_key = self._generate_metadata_key(key)
                metadata = self._client.get(metadata_key)

                if metadata and metadata.get('project_name') == project_name:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                metadata_key = self._generate_metadata_key(key)
                self._client.delete(key)
                self._client.delete(metadata_key)
                self._key_tracker.discard(key)
                invalidated_count += 1

            logger.info(f"Invalidated {invalidated_count} cache entries for project {project_name}")

        except Exception as e:
            logger.error(f"Failed to invalidate project cache: {e}")

        return invalidated_count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self._client:
            return {"error": "Not connected to memcached"}

        try:
            stats = self._client.stats()
            return {
                "memcached_stats": stats,
                "tracked_keys": len(self._key_tracker),
                "connected": True
            }
        except Exception as e:
            return {"error": str(e), "connected": False}

    def flush_all(self) -> bool:
        """Flush all cache data.

        Returns:
            True if successful
        """
        if not self._client:
            logger.error("Not connected to memcached")
            return False

        try:
            self._client.flush_all()
            self._key_tracker.clear()
            logger.info("Flushed all cache data")
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            return False
