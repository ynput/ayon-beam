"""Examples of dynamic cache configuration for AYON Beam addon."""

import asyncio
import json
from ayon_beam.cache_manager import (
    CacheService,
    CacheServiceConfig,
    CacheConfigManager,
    load_cache_config_from_file,
    update_cache_config_from_env
)


# Example 1: Programmatic Configuration
async def example_programmatic_config():
    """Example of updating cache configuration programmatically."""

    # Assuming you have a running cache service
    cache_service = None  # Your cache service instance

    # Method 1: Complete configuration replacement
    new_config = {
        "MyProject": ["folder_id_1", "folder_id_2", "folder_id_3"],
        "AnotherProject": ["folder_id_4", "folder_id_5"],
        "ThirdProject": ["folder_id_6"]
    }
    cache_service.update_cache_configuration(new_config)

    # Method 2: Add folders to specific project
    cache_service.add_folders_to_project(
        "MyProject",
        ["new_folder_1", "new_folder_2"],
        replace=False  # Merge with existing
    )

    # Method 3: Replace all folders for a project
    cache_service.add_folders_to_project(
        "MyProject",
        ["only_folder_1", "only_folder_2"],
        replace=True  # Replace existing
    )

    # Method 4: Remove specific folders
    cache_service.remove_folders_from_project(
        "MyProject",
        ["folder_to_remove_1", "folder_to_remove_2"]
    )

    # Method 5: Remove entire project
    cache_service.remove_folders_from_project("ProjectToRemove")

    # Trigger immediate prefetch after configuration changes
    await cache_service.trigger_immediate_prefetch()


# Example 2: Configuration from JSON File
async def example_json_config():
    """Example of loading configuration from JSON file."""

    # Create configuration file
    config_data = {
        "TestProject": [
            "73be773095dc11ee94a92dfcfd184dd9",
            "another-folder-id-here"
        ],
        "ProductionProject": [
            "prod-folder-1",
            "prod-folder-2",
            "prod-folder-3"
        ]
    }

    # Save to file
    with open("cache_config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    # Load and apply configuration
    cache_service = None  # Your cache service instance
    success = await load_cache_config_from_file(cache_service, "cache_config.json")

    if success:
        print("Configuration loaded successfully")


# Example 3: Configuration Manager with File Watching
async def example_config_manager():
    """Example using CacheConfigManager for advanced configuration management."""

    cache_service = None  # Your cache service instance

    # Create configuration manager
    config_manager = CacheConfigManager(cache_service, "beam_cache_config.json")

    # Add a watcher to be notified of configuration changes
    def on_config_change(new_config):
        print(f"Configuration changed: {len(new_config)} projects configured")
        for project, folders in new_config.items():
            print(f"  {project}: {len(folders)} folders")

    config_manager.add_config_watcher(on_config_change)

    # Start watching the configuration file for changes
    await config_manager.start_file_watcher("beam_cache_config.json", check_interval=5)

    # Update configuration from various sources

    # From dictionary
    config_manager.update_config_from_dict({
        "Project1": ["folder1", "folder2"],
        "Project2": ["folder3", "folder4"]
    })

    # From environment variables
    config_manager.update_config_from_env("BEAM_CACHE")

    # From API endpoint (if you have one)
    # await config_manager.update_config_from_api("https://your-api/cache-config")

    # Save current configuration to file
    await config_manager.save_config_to_file()

    # Let it run for a while...
    await asyncio.sleep(60)

    # Stop file watcher
    await config_manager.stop_file_watcher()


# Example 4: Environment Variable Configuration
def example_env_config():
    """Example of using environment variables for configuration."""

    import os

    # Set environment variables
    os.environ["BEAM_CACHE_TestProject"] = "folder1,folder2,folder3"
    os.environ["BEAM_CACHE_MyProject"] = "folder4,folder5"
    os.environ["BEAM_CACHE_ProductionProject"] = "folder6,folder7,folder8"

    # Apply configuration from environment
    cache_service = None  # Your cache service instance
    update_cache_config_from_env(cache_service, "BEAM_CACHE")


# Example 5: Dynamic Configuration via AYON Addon API
def example_addon_api():
    """Example of using BeamAddon methods for dynamic configuration."""

    # Assuming you have access to the BeamAddon instance
    beam_addon = None  # Your BeamAddon instance

    # Get current configuration
    current_config = beam_addon.get_cache_configuration()
    print(f"Current configuration: {current_config}")

    # Update entire configuration
    new_config = {
        "Project1": ["folder1", "folder2"],
        "Project2": ["folder3", "folder4"]
    }
    beam_addon.update_cache_configuration(new_config)

    # Add folders to specific project
    beam_addon.add_folders_to_project("Project1", ["folder5", "folder6"])

    # Get folders for a specific project
    project_folders = beam_addon.get_project_folders("Project1")
    print(f"Project1 folders: {project_folders}")

    # Remove specific folders
    beam_addon.remove_folders_from_project("Project1", ["folder2"])

    # Trigger immediate prefetch
    asyncio.create_task(beam_addon.trigger_immediate_prefetch("Project1"))


# Example 6: Configuration File Formats
def example_config_formats():
    """Examples of different configuration file formats supported."""

    # Format 1: Simple project -> folders mapping
    config_format_1 = {
        "TestProject": ["folder1", "folder2"],
        "MyProject": ["folder3", "folder4"]
    }

    # Format 2: Structured format with project objects
    config_format_2 = {
        "projects": [
            {
                "name": "TestProject",
                "folders": ["folder1", "folder2"]
            },
            {
                "name": "MyProject",
                "folders": ["folder3", "folder4"]
            }
        ]
    }

    # Format 3: Nested configuration
    config_format_3 = {
        "cache_config": {
            "TestProject": ["folder1", "folder2"],
            "MyProject": ["folder3", "folder4"]
        }
    }

    # All formats are supported by CacheConfigManager
    cache_service = None  # Your cache service instance
    config_manager = CacheConfigManager(cache_service)

    # Any of these will work
    config_manager.update_config_from_dict(config_format_1)
    config_manager.update_config_from_dict(config_format_2)
    config_manager.update_config_from_dict(config_format_3)


# Example 7: Real-world Integration Scenario
async def example_real_world_scenario():
    """Real-world example of dynamic cache configuration."""

    cache_service = None  # Your cache service instance
    config_manager = CacheConfigManager(cache_service)

    # Step 1: Start with environment-based configuration
    config_manager.update_config_from_env("BEAM_CACHE")

    # Step 2: Start file watcher for runtime updates
    await config_manager.start_file_watcher("runtime_config.json")

    # Step 3: Set up configuration change handler
    def on_project_opened(project_name, folder_ids):
        """Called when user opens a project in AYON."""
        print(f"Project {project_name} opened, adding to cache")
        cache_service.add_folders_to_project(project_name, folder_ids)

        # Immediately prefetch the new project
        asyncio.create_task(
            cache_service.trigger_immediate_prefetch(project_name, folder_ids)
        )

    def on_project_closed(project_name):
        """Called when user closes a project."""
        print(f"Project {project_name} closed, removing from cache")
        cache_service.remove_folders_from_project(project_name)

    # Step 4: Periodic configuration sync (e.g., from server)
    async def sync_config_from_server():
        while True:
            try:
                # Fetch updated configuration from your server
                # await config_manager.update_config_from_api("https://your-server/cache-config")
                pass
            except Exception as e:
                print(f"Failed to sync config: {e}")

            await asyncio.sleep(300)  # Sync every 5 minutes

    # Start background sync
    asyncio.create_task(sync_config_from_server())

    # Step 5: Save configuration periodically
    async def save_config_periodically():
        while True:
            await asyncio.sleep(1800)  # Every 30 minutes
            await config_manager.save_config_to_file()

    asyncio.create_task(save_config_periodically())


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_json_config())
    asyncio.run(example_config_manager())
    example_env_config()
    example_addon_api()
    example_config_formats()
    asyncio.run(example_real_world_scenario())
