from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json

from websocket_manager import manager

# Create the router
websocket_router = APIRouter(tags=["websockets"])

@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time chat
    - client_id: Optional identifier for the client
    - name: Optional display name for the client
    """
    # Connect the client
    await manager.connect(websocket, client_id)
    
    # Use provided name or default
    client_name = name or "Anonymous"
    
    try:
        # Notify client of successful connection
        await manager.send_message(
            websocket,
            {
                "type": "connection_status", 
                "status": "connected", 
                "client_id": client_id,
                "client_name": client_name
            }
        )
        
        # Notify others that someone joined (if client has an ID)
        if client_id:
            await manager.broadcast(
                {
                    "type": "client_joined", 
                    "client_id": client_id,
                    "client_name": client_name
                },
                exclude_client_id=client_id  # Don't send to the client that just joined
            )
        
        # Message handling loop
        while True:
            # Wait for messages from this client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping/pong to keep connection alive
                if message.get("type") == "pong":
                    continue
                
                # Extract message content
                content = message.get("content")
                recipient_id = message.get("recipient_id")
                
                if not content:
                    continue
                
                # Add sender information
                message["sender_id"] = client_id
                message["sender_name"] = client_name
                
                # Forward to specific recipient or broadcast
                if recipient_id:
                    # Direct message
                    await manager.send_to_client(recipient_id, message)
                else:
                    # Broadcast message
                    await manager.broadcast(message)
                
            except json.JSONDecodeError:
                # If not valid JSON, just broadcast as plain text
                await manager.broadcast({
                    "type": "message",
                    "content": data,
                    "sender_id": client_id,
                    "sender_name": client_name
                })
                
    except WebSocketDisconnect:
        # Handle disconnection
        manager.disconnect(websocket, client_id)
        
        # Notify others that client disconnected (if client had an ID)
        if client_id:
            await manager.broadcast({
                "type": "client_left", 
                "client_id": client_id,
                "client_name": client_name
            })
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)