from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey,Boolean,Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True,index=True, autoincrement=True)
    username = Column(String(50), unique=True)
    email = Column(String(80), unique=True)
    password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    orders = relationship('Order', back_populates='user')

    def __repr__(self):
        return f"<User {self.username}>"
    
class Order(Base):

    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Delivered', 'Delivered'),
        ('Canceled', 'Canceled')
    ]

    PIIZA_SIZE = [
        ('Small','Small'),
        ('Medium','Medium'),
        ('Large','Large')
    ]
    
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quantity = Column(Integer, nullable=False)
    order_status = Column(String, nullable=False, default='Pending')  
    pizza_size = Column(String, nullable=False, default='Small')  
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='orders')

    def __repr__(self):
        return f"<Order {self.id}>"

    

  

