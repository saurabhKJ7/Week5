from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for subscribers in self.subscriptions.values():
            subscribers.discard(websocket)

    async def subscribe(self, symbol: str, websocket: WebSocket):
        """Subscribe a websocket connection to a specific stock symbol."""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].add(websocket)

    async def unsubscribe(self, symbol: str, websocket: WebSocket):
        """Unsubscribe a websocket connection from a specific stock symbol."""
        if symbol in self.subscriptions:
            self.subscriptions[symbol].discard(websocket)

    async def broadcast_to_symbol(self, symbol: str, message: dict):
        """Broadcast a message to all subscribers of a specific symbol."""
        if symbol not in self.subscriptions:
            return
        
        message_with_timestamp = {
            **message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection in self.subscriptions[symbol]:
            try:
                await connection.send_json(message_with_timestamp)
            except Exception:
                # If sending fails, we'll handle it in the main websocket loop
                pass

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # If sending fails, we'll handle it in the main websocket loop
                pass

    def get_subscribers_count(self, symbol: str) -> int:
        """Get the number of subscribers for a specific symbol."""
        return len(self.subscriptions.get(symbol, set())) 