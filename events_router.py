from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Security
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Message, User, Admin
from schema import MessageSchema, WebSocketMessage
from database import SessionLocal
from websocket_manager import manager
from auth_router import get_current_user, get_current_admin, UserInDB, AdminInDB, get_currentUser, get_currentAdmin

events_router = APIRouter(tags=["messages"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/send")
async def admin_send_message(
    message: WebSocketMessage,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: AdminInDB = Depends(get_current_admin)
):
    """Admin endpoint to send a message to a specific user or broadcast to all users"""
    
    # Set sender details
    sender_id = f"admin_{current_admin.id}"
    sender_name = current_admin.username
    
    # Store in database
    db_message = Message(
        content=message.content,
        sender_id=sender_id,
        sender_name=sender_name,
        admin_id=current_admin.id,
        is_broadcast=False if message.recipient_id else True
    )
    
    # Handle recipient if provided
    if message.recipient_id:
        # Validate recipient format
        if not message.recipient_id.startswith("user_"):
            return {"message": "Invalid recipient ID format. Must be in format 'user_X'", "success": False}
        
        try:
            recipient_id = int(message.recipient_id.split("_")[1])
            # Verify user exists
            user = db.query(User).filter(User.id == recipient_id).first()
            if not user:
                return {"message": "Recipient user not found", "success": False}
                
            # Set recipient in database
            db_message.recipient_id = recipient_id
            
        except (ValueError, IndexError):
            return {"message": "Invalid recipient ID format", "success": False}
    
    # Save message to database
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Handle broadcast or direct message
    if message.recipient_id:
        # Send via WebSocket if client is connected
        success = await manager.send_to_client(
            message.recipient_id,
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
    else:
        # This is a broadcast
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

@admin_router.get("/history", response_model=List[MessageSchema])
async def admin_get_message_history(
    recipient_id: Optional[str] = None,
    broadcast_only: bool = False,
    db: Session = Depends(get_db),
    current_admin: AdminInDB = Depends(get_current_admin)
):
    """Admin endpoint to get message history, either all broadcasts or filtered by recipient_id"""
    
    # Set up base query
    query = db.query(Message)
    
    if broadcast_only:
        # Only get broadcast messages
        query = query.filter(Message.is_broadcast == True)
    elif recipient_id:
        # Filter by recipient if specified
        if recipient_id.startswith("user_"):
            try:
                user_id = int(recipient_id.split("_")[1])
                query = query.filter(
                    or_(
                        # Messages from admin to specified user
                        (Message.admin_id == current_admin.id) & (Message.recipient_id == user_id),
                        # Messages from specified user to this admin
                        (Message.user_id == user_id) & (Message.admin_id == current_admin.id)
                    )
                )
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid recipient ID format")
        else:
            # If not a valid recipient format, return empty list
            return []
    else:
        # Get all messages involving this admin
        query = query.filter(
            or_(
                Message.admin_id == current_admin.id,
                Message.is_broadcast == True
            )
        )
    
    messages = query.order_by(Message.timestamp.desc()).all()
    return messages

# User endpoints
user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.post("/send")
async def user_send_message(
    message: WebSocketMessage,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """User endpoint to send a message to a specific admin"""
    
    # Set sender details
    sender_id = f"user_{current_user.id}"
    sender_name = current_user.username
    
    # Users can only send to admins and cannot broadcast
    admin = db.query(Admin).first()
    if not admin:
        return {"message": "Admin not found", "success": False}

    recipient_id = f"admin_{admin.id}"
    
    # Store in database
    db_message = Message(
        content=message.content,
        sender_id=sender_id,
        sender_name=sender_name,
        user_id=current_user.id,
        admin_id=admin.id,
        is_broadcast=False
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Send via WebSocket if client is connected
    success = await manager.send_to_client(
        message.recipient_id,
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
        "message": "Message sent to admin", 
        "success": success, 
        "message_id": db_message.id
    }

@user_router.get("/history", response_model=List[MessageSchema])
async def user_get_message_history(
    broadcast_only: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """User endpoint to get message history, either all broadcasts or conversation with default admin (admin_id=1)"""

    query = db.query(Message)

    if broadcast_only:
        query = query.filter(Message.is_broadcast == True)
    else:
        # Only one admin with id=1
        admin_id_num = 1
        query = query.filter(
            or_(
                # Messages from user to admin
                (Message.user_id == current_user.id) & (Message.admin_id == admin_id_num),
                # Messages from admin to this user
                (Message.admin_id == admin_id_num) & (Message.recipient_id == current_user.id),
                # Broadcast messages
                Message.is_broadcast == True
            )
        )

    messages = query.order_by(Message.timestamp.desc()).all()
    return messages

# Add the routers to the main router
events_router.include_router(admin_router)
events_router.include_router(user_router)