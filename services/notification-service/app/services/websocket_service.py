# app/services/websocket_service.py
# WebSocket notification service

import asyncio
from typing import Set

import structlog

logger = structlog.get_logger()


class WebSocketService:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        self.connections: Set = set()
        self.user_connections: dict = {}
    
    async def connect(self, websocket, user_id: str = None):
        """Register new connection."""
        self.connections.add(websocket)
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        logger.info("websocket_connected", user_id=user_id)
    
    async def disconnect(self, websocket, user_id: str = None):
        """Remove connection."""
        self.connections.discard(websocket)
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
        logger.info("websocket_disconnected", user_id=user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast to all connections."""
        disconnected = set()
        for conn in self.connections:
            try:
                await conn.send_json(message)
            except Exception:
                disconnected.add(conn)
        
        # Clean up disconnected
        for conn in disconnected:
            await self.disconnect(conn)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send to specific user."""
        if user_id not in self.user_connections:
            return
        
        disconnected = set()
        for conn in self.user_connections[user_id]:
            try:
                await conn.send_json(message)
            except Exception:
                disconnected.add(conn)
        
        for conn in disconnected:
            await self.disconnect(conn, user_id)