"""WebSocket client for receiving cache invalidation events from AYON server."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException


logger = logging.getLogger(__name__)


@dataclass
class InvalidationEvent:
    """Cache invalidation event."""
    event_type: str  # 'folder_updated', 'project_updated', 'entity_deleted'
    project_name: str
    folder_id: Optional[str] = None
    entity_id: Optional[str] = None
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InvalidationEvent':
        """Create event from dictionary."""
        return cls(
            event_type=data.get('event_type', 'unknown'),
            project_name=data.get('project_name', ''),
            folder_id=data.get('folder_id'),
            entity_id=data.get('entity_id'),
            timestamp=data.get('timestamp')
        )


class WebSocketClient:
    """WebSocket client for receiving cache invalidation events."""

    def __init__(self, server_url: str, api_key: str):
        """Initialize WebSocket client.

        Args:
            server_url: AYON server URL
            api_key: API key for authentication
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.ws_url = self.server_url.replace('http://', 'ws://').replace('https://', 'wss://')
        self.ws_url = f"{self.ws_url}/ws/events"

        self._websocket = None
        self._running = False
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60
        self._event_handlers: List[Callable[[InvalidationEvent], None]] = []

    def add_event_handler(self, handler: Callable[[InvalidationEvent], None]):
        """Add an event handler for invalidation events.

        Args:
            handler: Function to call when an event is received
        """
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: Callable[[InvalidationEvent], None]):
        """Remove an event handler.

        Args:
            handler: Handler function to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message.

        Args:
            message: Raw message string
        """
        try:
            data = json.loads(message)

            # Check if it's a cache invalidation event
            if data.get('type') == 'cache_invalidation':
                event = InvalidationEvent.from_dict(data.get('payload', {}))
                logger.debug(f"Received invalidation event: {event.event_type} for {event.project_name}")

                # Notify all handlers
                for handler in self._event_handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def _connect(self) -> bool:
        """Establish WebSocket connection.

        Returns:
            True if connection successful
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            self._websocket = await websockets.connect(
                self.ws_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )

            logger.info(f"Connected to WebSocket at {self.ws_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False

    async def _listen(self):
        """Listen for WebSocket messages."""
        try:
            async for message in self._websocket:
                await self._handle_message(message)

        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket listener: {e}")

    async def start(self):
        """Start the WebSocket client with auto-reconnect."""
        self._running = True
        reconnect_delay = self._reconnect_delay

        while self._running:
            try:
                if await self._connect():
                    reconnect_delay = self._reconnect_delay  # Reset delay on successful connection
                    await self._listen()

                if not self._running:
                    break

                logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)

                # Exponential backoff with max limit
                reconnect_delay = min(reconnect_delay * 2, self._max_reconnect_delay)

            except Exception as e:
                logger.error(f"WebSocket client error: {e}")
                await asyncio.sleep(reconnect_delay)

    async def stop(self):
        """Stop the WebSocket client."""
        self._running = False

        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        logger.info("WebSocket client stopped")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected.

        Returns:
            True if connected
        """
        return self._websocket is not None and not self._websocket.closed
