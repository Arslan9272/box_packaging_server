from typing import Dict, List, Optional
from fastapi import WebSocket
import json
from datetime import datetime, timedelta
import asyncio

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.anonymous_clients: List[WebSocket] = []
        self.last_ping: Dict[WebSocket, datetime] = {}

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Connect a new websocket client"""
        await websocket.accept()
        self.last_ping[websocket] = datetime.now()
        
        if client_id:
            # If there's an existing connection with this ID, close it
            if client_id in self.connections:
                old_ws = self.connections[client_id]
                await self._safe_close(old_ws)
            self.connections[client_id] = websocket
        else:
            self.anonymous_clients.append(websocket)
        
        # Start ping task if not already running
        if not hasattr(self, '_ping_task'):
            self._ping_task = asyncio.create_task(self._ping_clients())
    
    async def _safe_close(self, websocket: WebSocket):
        """Safely close a websocket connection"""
        try:
            await websocket.close()
        except Exception:
            pass
        finally:
            self._cleanup_ws(websocket)

    def _cleanup_ws(self, websocket: WebSocket):
        """Remove websocket from all connection tracking"""
        if websocket in self.last_ping:
            del self.last_ping[websocket]
        
        # Remove from client connections
        for client_id, ws in list(self.connections.items()):
            if ws == websocket:
                del self.connections[client_id]
        
        # Remove from anonymous clients
        if websocket in self.anonymous_clients:
            self.anonymous_clients.remove(websocket)

    async def _ping_clients(self):
        """Regularly ping connected clients to keep connections alive"""
        while True:
            try:
                now = datetime.now()
                to_remove = []
                
                # Check all connections
                for ws in list(self.last_ping.keys()):
                    # Send ping to active connections
                    try:
                        if now - self.last_ping[ws] > timedelta(seconds=30):
                            await ws.send_text(json.dumps({"type": "ping"}))
                            self.last_ping[ws] = now
                    except Exception:
                        to_remove.append(ws)
                
                # Clean up dead connections
                for ws in to_remove:
                    self._cleanup_ws(ws)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Ping task error: {e}")
                await asyncio.sleep(10)
    
    def disconnect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Disconnect a websocket client"""
        if client_id and client_id in self.connections:
            del self.connections[client_id]
        elif websocket in self.anonymous_clients:
            self.anonymous_clients.remove(websocket)
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific websocket"""
        try:
            await websocket.send_text(json.dumps(message))
            return True
        except Exception:
            return False
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send a message to a specific client by ID"""
        if client_id in self.connections:
            return await self.send_message(self.connections[client_id], message)
        return False
    
    async def broadcast(self, message: dict, exclude_client_id: Optional[str] = None):
        """Send a message to all connected clients, optionally excluding one client"""
        disconnected_clients = []
        
        # Send to identified clients
        for client_id, websocket in self.connections.items():
            if client_id != exclude_client_id:
                success = await self.send_message(websocket, message)
                if not success:
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.connections:
                del self.connections[client_id]
        
        # Send to anonymous clients
        still_connected = []
        for websocket in self.anonymous_clients:
            success = await self.send_message(websocket, message)
            if success:
                still_connected.append(websocket)
        
        self.anonymous_clients = still_connected
        
        # Return total number of recipients
        return len(self.connections) + len(self.anonymous_clients)
    
    async def get_connected_clients(self):
        """Get list of connected client IDs"""
        return {
            "connected_clients": list(self.connections.keys()),
            "anonymous_clients_count": len(self.anonymous_clients),
            "total_clients": len(self.connections) + len(self.anonymous_clients)
        }

# Create a global instance
manager = WebSocketManager()