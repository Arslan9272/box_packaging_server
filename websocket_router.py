from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from typing import Optional
import json
from websocket_manager import manager
from auth_router import verify_token
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Admin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the router
websocket_router = APIRouter(tags=["websockets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@websocket_router.websocket("/ws/admin")
async def admin_websocket_endpoint(
    websocket: WebSocket, 
    token: str = Query(..., description="Authentication token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat
    - token: Authentication token required to identify the user or admin
    """
    # Verify token and get payload
    try:
        payload = verify_token(token)
        if payload.get("type") != "admin":
            await websocket.close(code=1008, reason="Admin access required")
            return
              
        admin_id = payload.get("sub")
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            await websocket.close(code=1008, reason="Admin not found")
            return
        client_id = f"admin_{admin.id}"

        await websocket.accept()
        await manager.connect(websocket, client_id)

        
      
    
        try:
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection_status",
                "status": "connected",
                "client_id": client_id,
                "client_name": admin.username
            })
        
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    
                    # Handle ping (no response needed for pings)
                    if message.get("type") == "ping":
                        continue
                        
                    # Process admin messages
                    if message.get("type") == "message_to_client":
                        recipient_id = message.get("recipient_id")
                        if not recipient_id or not recipient_id.startswith("user_"):
                            await websocket.send_json({
                                "type": "error",
                                "message": "Invalid recipient ID"
                            })
                            continue
                            
                        # Forward message to recipient
                        success = await manager.send_to_client(
                            recipient_id,
                            {
                                "type": "admin_message",
                                "content": message.get("content"),
                                "admin_id": admin.id,
                                "admin_name": admin.username,
                                "timestamp": datetime.datetime.utcnow().isoformat()
                            }
                        )
                        
                        if not success:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Recipient not connected"
                            })

                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid message format"
                    })

        except WebSocketDisconnect:
            logger.info(f"Admin disconnected: {client_id}")
        finally:
            manager.disconnect(websocket, client_id)

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
        