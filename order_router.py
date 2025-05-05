from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models import Order
from schema import UserSchema, OrderModel
from database import SessionLocal
from auth_router import get_current_user

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

@order_router.get("/get_order", response_model=List[OrderModel])
async def get_orders(current_user: UserSchema = Depends(get_current_user), db=Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    return orders  

@order_router.post("/place_order", response_model=OrderModel)
async def place_order(order: OrderModel, current_user: UserSchema = Depends(get_current_user), db=Depends(get_db)):
    new_order = Order(
        quantity=order.quantity,
        order_status=order.order_status,
        pizza_size=order.pizza_size,
        user_id=current_user.id  
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order) 
    return new_order

@order_router.put("/update_order/{order_id}", response_model=OrderModel)
async def update_order( order:OrderModel, order_id:int, current_user: UserSchema = Depends(get_current_user),db=Depends(get_db)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db_order.quantity = order.quantity
    db_order.order_status = order.order_status
    db_order.pizza_size = order.pizza_size
    db.commit()
    db.refresh(db_order)
    return db_order


@order_router.delete("/delete_order/{order_id}")
async def delete_order(order_id :int, current_user:UserSchema=Depends(get_current_user), db=Depends(get_db)):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(db_order)
    db.commit()
    return {"message":"Order deleted successfully"}