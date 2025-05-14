from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType
from database import Base
import datetime

class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True)
    email = Column(String(80), unique=True)
    password = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    orders = relationship('Order', back_populates='admin')
    messages = relationship('Message', foreign_keys='Message.admin_id', back_populates='admin')
    notifications = relationship('Notification', back_populates='admin')

    def __repr__(self):
        return f"<Admin {self.username}>"

class User(Base):  
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True)
    email = Column(String(80), unique=True)
    orders = relationship('Order', back_populates='user')
    messages_sent = relationship('Message', foreign_keys='Message.user_id', back_populates='user')
    messages_received = relationship('Message', foreign_keys='Message.recipient_id', back_populates='recipient')
    notifications = relationship('Notification', back_populates='user')

    def __repr__(self):
        return f"<User {self.username}>"

class Order(Base):
    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Delivered', 'Delivered'),
        ('Canceled', 'Canceled')
    ]
    
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone_no = Column(String(20), nullable=False)
    email_address = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    color = Column(String(50))
    product_name = Column(String(100), nullable=False)
    size_length = Column(Float)
    size_width = Column(Float)
    size_depth = Column(Float)
    message = Column(Text)
    order_status = Column(String(50), nullable=False, default='Pending')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship('User', back_populates='orders')
    admin = relationship('Admin', back_populates='orders')

    def __repr__(self):
        return f"<Order {self.id}>"

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text, nullable=False)
    sender_id = Column(String(50), nullable=True)  # ID or username of sender
    sender_name = Column(String(100), nullable=True)  # Name of sender
    is_broadcast = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Message {self.id}>"

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=True)
    
    user = relationship('User', back_populates='notifications')
    admin = relationship('Admin', back_populates='notifications')
    
    def __repr__(self):
        return f"<Notification {self.id}>"