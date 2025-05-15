from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth_router import auth_router
from order_router import order_router
from websocket_router import websocket_router
from database import engine, Base
from dotenv import load_dotenv
import os
from events_router import events_router

load_dotenv()

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order Management API",
    description="API for managing orders with real-time websocket communication"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Create React App
        "http://localhost:8000",  # Possible other frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Register routers
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(websocket_router)
app.include_router(events_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Order Management API!"}
