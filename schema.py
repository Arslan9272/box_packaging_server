from pydantic import BaseModel
from typing import Optional

class UserSchema(BaseModel):
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
                "is_staff": False
            }
        }


class LoginModel(BaseModel):
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


class OrderModel(BaseModel):
    id: Optional[int] = None
    quantity: int
    order_status: Optional[str] = "Pending"
    pizza_size: Optional[str] = "Small"
    user_id: Optional[int] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "quantity": 2,
                "order_status": "Pending",
                "pizza_size": "Small",
                "user_id": 1
            }
        }
