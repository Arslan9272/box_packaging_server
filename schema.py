from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AdminSchema(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    email: str
    password: str
    is_active: Optional[bool] = False
    is_staff: Optional[bool] = False

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "username": "user1",
                "email": "example@example.com",
                "password": "password123",
                "is_active": True,
                "is_staff": False,
            }
        }

class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "username": "user1",
                "email": "example@example.com"
            }
        }

class LoginUserModel(BaseModel):
    email: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "email": "user1@gmail.com"
            }
        }


class LoginAdminModel(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "email": "user1@gmail.com",
                "password": "password123"
            }
        }


class OrderCreateModel(BaseModel):
    name : str
    phone_no: str
    email_address: str
    quantity: int
    color: Optional[str] = None
    product_name: str
    size_length: Optional[float] = None
    size_width: Optional[float] = None
    size_depth: Optional[float] = None
    message: Optional[str] = None
    order_status: Optional[str] = "Pending"

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "John Doe",
                "phone_no": "1234567890",
                "email_address": "john@example.com",
                "quantity": 2,
                "color": "Red",
                "product_name": "Custom T-shirt",
                "size_length": 28.5,
                "size_width": 18.0,
                "size_depth": 0.5,
                "message": "Please deliver before Monday",
                "order_status": "Pending",
            }
        }
class OrderModel(OrderCreateModel):
    id: int
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MessageSchema(BaseModel):
    id: Optional[int] = None
    content: str
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    is_broadcast: Optional[bool] = False
    timestamp: Optional[datetime] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "content": "Hello, how can I help you?",
                "sender_id": "user123",
                "sender_name": "John Doe",
                "is_broadcast": False
            }
        }

class WebSocketMessage(BaseModel):
    content: str
    client_id: Optional[str] = None
    sender_name: Optional[str] = None



class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    
    class Config:
        orm_mode = True

class AdminBase(BaseModel):
    username: str
    email: str

class AdminCreate(AdminBase):
    password: str

class AdminInDB(AdminBase):
    id: int
    is_active: bool
    is_staff: bool
    
    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    content: str
    
class WebSocketMessage(MessageBase):
    recipient_id: Optional[str] = None
    sender_name: Optional[str] = None
    
class MessageSchema(BaseModel):
    id: int
    content: str
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    admin_id: Optional[int] = None
    user_id: Optional[int] = None
    recipient_id: Optional[int] = None
    is_broadcast: bool
    timestamp: datetime
    
    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str  # "user" or "admin"
    user_id: int
    username: str