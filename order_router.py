from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from models import Order
from schema import UserSchema, OrderModel
from database import SessionLocal
from auth_router import get_current_user
from websocket_manager import manager

order_router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





@order_router.get("/", response_model=List[OrderModel])
async def get_orders(db=Depends(get_db)):
    orders = db.query(Order).all()
    return orders

@order_router.get("/status/{status}", response_model=List[OrderModel])
async def get_orders_by_status(
    status: str,
    current_user: UserSchema = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get orders by status"""
    if current_user.is_staff:
        orders = db.query(Order).filter(Order.order_status == status).all()
    else:
        orders = db.query(Order).filter(
            Order.order_status == status,
            Order.user_id == current_user.id
        ).all()
    return orders

@order_router.get("/{order_id}", response_model=OrderModel)
async def get_order(
    order_id: int, 
    current_user: UserSchema = Depends(get_current_user),
    db=Depends(get_db)
):
    """Get a specific order by ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if user is authorized to view this order
    if not current_user.is_staff and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    
    return order

@order_router.post("/create", response_model=OrderModel)
async def create_order(
    order: OrderModel,
    db=Depends(get_db)
):
    """Create an order with authenticated user"""
    new_order = Order(
        name=order.name,
        phone_no=order.phone_no,
        email_address=order.email_address,
        quantity=order.quantity,
        color=order.color,
        product_name=order.product_name,
        size_length=order.size_length,
        size_width=order.size_width,
        size_depth=order.size_depth,
        message=order.message,
        order_status="Pending",  
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    
    
    return new_order