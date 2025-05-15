
from database import Base, engine
from models import User, Order,Message,Admin

Base.metadata.create_all(bind=engine)