from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Message
from schema import MessageSchema, WebSocketMessage
from database import SessionLocal
from websocket_manager import manager

events_router = APIRouter(prefix="/messages", tags=["messages"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@events_router.post("/send")
async def send_message(
    message: WebSocketMessage,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send a message to a specific client or broadcast to all clients"""
    
    # Use sender name or default to "Anonymous"
    sender_name = message.sender_name or "Anonymous"
    sender_id = message.sender_name or "anonymous"
    
    # Message to a specific client
    if message.client_id:
        # Store in database
        db_message = Message(
            content=message.content,
            sender_id=sender_id,
            sender_name=sender_name,
            is_broadcast=False
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Send via WebSocket if client is connected
        success = await manager.send_to_client(
            message.client_id,
            {
                "type": "direct_message",
                "content": message.content,
                "sender_name": sender_name,
                "sender_id": sender_id,
                "message_id": db_message.id,
                "timestamp": db_message.timestamp.isoformat()
            }
        )
        
        return {
            "message": "Message sent to recipient", 
            "success": success, 
            "message_id": db_message.id
        }
    
    # Broadcast message
    if message.content:
        # Save broadcast message
        db_message = Message(
            content=message.content,
            sender_id=sender_id,
            sender_name=sender_name,
            is_broadcast=True
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Broadcast to all connected clients
        recipients_count = await manager.broadcast(
            {
                "type": "broadcast",
                "content": message.content,
                "sender_name": sender_name,
                "sender_id": sender_id,
                "message_id": db_message.id,
                "timestamp": db_message.timestamp.isoformat()
            }
        )
        
        return {
            "message": f"Broadcast sent to {recipients_count} clients", 
            "success": True,
            "message_id": db_message.id
        }
    
    return {"message": "No content provided", "success": False}

@events_router.get("/history", response_model=List[MessageSchema])
async def get_message_history(
    client_id: Optional[str] = None,
    broadcast_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get message history, either all broadcasts or filtered by client_id"""
    query = db.query(Message)
    
    if broadcast_only:
        # Only get broadcast messages
        query = query.filter(Message.is_broadcast == True)
    elif client_id:
        # Get direct messages involving the given client
        query = query.filter(
            (Message.sender_id == client_id) | 
            (Message.is_broadcast == True)
        )
    
    messages = query.order_by(Message.timestamp.desc()).all()
    return messages