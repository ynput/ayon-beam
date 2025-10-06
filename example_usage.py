"""Example usage of the AYON Beam caching service."""

import asyncio
import os
import logging
from ayon_beam.cache_manager import (
    CacheService, 
    CacheServiceConfig, 
    RateLimitConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example of using the cache service."""
    
    # Example configuration
    config = CacheServiceConfig(
        server_url="https://your-ayon-server.com",
        api_key="your-api-key",
        memcache_host="localhost",
        memcache_port=11211,
        default_ttl=3600,  # 1 hour
        rate_limit_config=RateLimitConfig(
            requests_per_second=5.0,
            burst_limit=10,
            cooldown_period=60.0,
            per_project_limit=2.0
        ),
        prefetch_interval=300,  # 5 minutes
        max_concurrent_fetches=5,
        projects_to_cache=["TestProject"],
        folders_to_cache={
            "TestProject": ["73be773095dc11ee94a92dfcfd184dd9"]
        }
    )
    
    # Create and start the cache service
    cache_service = CacheService(config)
    
    try:
        await cache_service.start()
        logger.info("Cache service started")

        # Example: Get folder data
        folder_data = await cache_service.get_folder_data(
            project_name="TestProject",
            folder_id="73be773095dc11ee94a92dfcfd184dd9"
        )

        if folder_data:
            logger.info(f"Retrieved folder data: {folder_data.get('name', 'Unknown')}")

            # Print products
            products = folder_data.get('products', {}).get('edges', [])
            logger.info(f"Found {len(products)} products")
            for product in products:
                node = product.get('node', {})
                logger.info(f"  - Product: {node.get('name')} ({node.get('productType')})")

            # Print tasks
            tasks = folder_data.get('tasks', {}).get('edges', [])
            logger.info(f"Found {len(tasks)} tasks")
            for task in tasks:
                node = task.get('node', {})
                logger.info(f"  - Task: {node.get('name')} ({node.get('taskType')})")

        # Get service statistics
        stats = cache_service.get_service_stats()
        logger.info(f"Service stats: {stats}")

        # Let it run for a bit to see prefetching in action
        logger.info("Letting service run for 60 seconds...")
        await asyncio.sleep(60)

    except Exception as e:
        logger.error(f"Error running cache service: {e}")

    finally:
        await cache_service.stop()
        logger.info("Cache service stopped")


if __name__ == "__main__":
    asyncio.run(main())
