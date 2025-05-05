from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth_router import auth_router
from order_router import order_router
from dotenv import load_dotenv
import os

load_dotenv() 

app = FastAPI()

origins = [
    "http://localhost:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

app.include_router(auth_router)
app.include_router(order_router)
