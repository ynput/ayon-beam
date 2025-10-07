# AYON Beam Caching Service

The AYON Beam addon provides smart caching and entity-centric API for AYON hierarchy data using GraphQL, memcached, and WebSocket-based cache invalidation.

## Features

- **GraphQL Client**: Fetches data from AYON server using GraphQL queries
- **Memcached Storage**: Local caching using pymemcache for fast data retrieval
- **WebSocket Events**: Real-time cache invalidation based on server events
- **Rate Limiting**: Intelligent rate limiting to prevent server overload
- **Pre-fetching**: Background pre-fetching of configured projects and folders
- **Smart Invalidation**: Selective cache invalidation based on entity updates

## Configuration

The service is configured through environment variables:

### Required Settings

```bash
# AYON server connection
AYON_SERVER_URL=https://your-ayon-server.com
AYON_API_KEY=your-api-key-here
```

### Optional Settings

```bash
# Memcached configuration
AYON_BEAM_MEMCACHE_HOST=localhost
AYON_BEAM_MEMCACHE_PORT=11211

# Rate limiting
AYON_BEAM_RATE_LIMIT_RPS=5.0          # Requests per second (global)
AYON_BEAM_BURST_LIMIT=10              # Burst limit
AYON_BEAM_COOLDOWN_PERIOD=60.0        # Cooldown after hitting limits (seconds)
AYON_BEAM_PROJECT_RATE_LIMIT=2.0      # Requests per second per project

# Caching settings
AYON_BEAM_DEFAULT_TTL=3600            # Default cache TTL (seconds)
AYON_BEAM_PREFETCH_INTERVAL=300       # Pre-fetch interval (seconds)
AYON_BEAM_MAX_CONCURRENT=5            # Max concurrent fetches

# Projects and folders to cache
AYON_BEAM_PROJECTS=TestProject,AnotherProject
AYON_BEAM_FOLDERS_TestProject=folder_id_1,folder_id_2
AYON_BEAM_FOLDERS_AnotherProject=folder_id_3,folder_id_4
```

## Usage

### As AYON Addon (Tray Service)

The service automatically starts when the AYON tray is launched and the Beam addon is enabled:

1. Set the required environment variables
2. Start AYON tray
3. The Beam addon will initialize and start caching configured projects/folders

### Programmatic Usage

```python
import asyncio
from ayon_beam.cache_manager import CacheService, CacheServiceConfig, RateLimitConfig

async def example():
    config = CacheServiceConfig(
        server_url="https://your-ayon-server.com",
        api_key="your-api-key",
        memcache_host="localhost",
        memcache_port=11211,
        projects_to_cache=["TestProject"],
        folders_to_cache={"TestProject": ["folder_id_here"]}
    )
    
    service = CacheService(config)
    await service.start()
    
    # Get folder data (from cache or server)
    data = await service.get_folder_data("TestProject", "folder_id_here")
    
    await service.stop()

asyncio.run(example())
```

### API Methods

```python
# Get folder data with products and tasks
data = await addon.get_folder_data("ProjectName", "folder_id")

# Force refresh from server
data = await addon.get_folder_data("ProjectName", "folder_id", force_refresh=True)

# Add project to caching list
addon.add_project_to_cache("NewProject", ["folder1", "folder2"])

# Remove project from caching
addon.remove_project_from_cache("OldProject")

# Get service statistics
stats = addon.get_service_stats()
```

## GraphQL Query Structure

The service uses this GraphQL query to fetch folder data:

```graphql
query MyQuery($projectName: String!, $folderId: String!) {
  project(name: $projectName) {
    folder(id: $folderId) {
      id
      name
      path
      folderType
      products {
        edges {
          node {
            id
            productType
            productBaseType
            path
            name
            data
            active
            type
          }
        }
      }
      tasks {
        edges {
          node {
            id
            label
            name
            path
            status
            tags
            taskType
            updatedAt
          }
        }
      }
    }
  }
}
```

## Cache Invalidation Events

The service listens for these WebSocket events for cache invalidation:

- `folder_updated`: Invalidates specific folder cache
- `project_updated`: Invalidates entire project cache
- `entity_deleted`: Invalidates related folder cache

## Dependencies

Required Python packages:

- `pymemcache>=4.0.0` - Memcached client
- `aiohttp>=3.8.0` - HTTP client for GraphQL
- `websockets>=11.0.0` - WebSocket client for events

## Installation

1. Install memcached server:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install memcached
   
   # macOS
   brew install memcached
   
   # Windows (using Chocolatey)
   choco install memcached
   ```

2. Start memcached:
   ```bash
   memcached -d -m 64 -p 11211
   ```

3. Set environment variables and restart AYON tray

## Monitoring

Use `get_service_stats()` to monitor:

- Cache hit/miss rates
- Rate limiting statistics  
- Memcached connection status
- WebSocket connection status
- Pre-fetch cycle statistics

## Troubleshooting

### Common Issues

1. **Cache service not starting**
   - Check `AYON_SERVER_URL` and `AYON_API_KEY` environment variables
   - Verify memcached is running and accessible

2. **High cache miss rate**
   - Increase `BEAM_DEFAULT_TTL`
   - Add more folders to pre-fetch configuration
   - Check rate limiting settings

3. **Rate limiting issues**
   - Adjust `BEAM_RATE_LIMIT_RPS` and `BEAM_PROJECT_RATE_LIMIT`
   - Increase `BEAM_BURST_LIMIT` for bursty workloads
   - Monitor cooldown periods

4. **WebSocket connection issues**
   - Check server WebSocket endpoint availability
   - Verify API key has WebSocket permissions
   - Check firewall/network settings
