from fastapi import APIRouter, HTTPException, status, Depends, Body
from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer
from schema import UserSchema, LoginAdminModel, AdminSchema, LoginUserModel
from database import SessionLocal
from models import User, Admin
from pydantic import BaseModel
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from jose import jwt, JWTError  
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    username: Optional[str] = None
    type: Optional[str] = None  # "user" or "admin"

class UserInDB(BaseModel):
    id: int
    username: str
    email: str

class AdminInDB(BaseModel):
    id: int
    username: str
    email: str
    is_staff: bool
    is_active: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> UserInDB:
    """Get current user from token"""
    try:
        payload = verify_token(token)
        
        # Extract username and type from token
        username = payload.get("sub")
        user_type = payload.get("type")
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        # Check if this is a user token
        if user_type == "user" or user_type is None:
            # Try to find user by email first (for backward compatibility)
            user = db.query(User).filter(User.email == username).first()
            
            # If not found, try by username
            if not user:
                user = db.query(User).filter(User.username == username).first()
                
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
                
            return UserInDB(
                id=user.id,
                username=user.username,
                email=user.email
            )
        
        raise HTTPException(status_code=403, detail="Not authenticated as user")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


async def get_current_admin(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> AdminInDB:
    """Get current admin from token"""
    try:
        payload = verify_token(token)
        
        # Extract username and type from token
        username = payload.get("sub")
        user_type = payload.get("type")
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        # Check if this is an admin token
        if user_type == "admin" or user_type is None:
            # Try to find admin by email first (for backward compatibility)
            admin = db.query(Admin).filter(Admin.email == username).first()
            
            # If not found, try by username
            if not admin:
                admin = db.query(Admin).filter(Admin.username == username).first()
                
            if not admin:
                raise HTTPException(status_code=401, detail="Admin not found")
                
         
                
            return AdminInDB(
                id=admin.id,
                username=admin.username,
                email=admin.email,
                is_staff=admin.is_staff,
                is_active=admin.is_active
            )
        
        raise HTTPException(status_code=403, detail="Not authenticated as admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# For backward compatibility with events_router.py
get_currentUser = get_current_user
get_currentAdmin = get_current_admin


@auth_router.post("/signup", response_model=AdminSchema, status_code=status.HTTP_201_CREATED)
async def signup(user: AdminSchema, db=Depends(get_db)):
    db_email = db.query(Admin).filter(Admin.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    db_username = db.query(Admin).filter(Admin.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    new_user = Admin(
        username=user.username,
        email=user.email,
        password=generate_password_hash(user.password),
        is_active=user.is_active,
        is_staff=user.is_staff
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@auth_router.post("/login")
async def login(form_data: LoginAdminModel = Body(...), db=Depends(get_db)):
    user = db.query(Admin).filter(Admin.email == form_data.email).first()
    if not user or not check_password_hash(user.password, form_data.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={
        "sub": user.email,
        "type": "admin"  
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_type": "admin",
        "username": user.username
    }


@auth_router.post("/user/signup", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def signup(user: UserSchema, db=Depends(get_db)):
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    db_username = db.query(User).filter(User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    new_user = User(
        username=user.username,
        email=user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/user/login")
async def login(form_data: LoginUserModel = Body(...), db=Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(data={
        "sub": user.email,
        "type": "user"  # Add type field for better token validation
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_type": "user",
        "email": user.email,
        "username": user.username
    }

@auth_router.get("/users", response_model=List[UserSchema])
async def get_all_users(db=Depends(get_db), current_admin: AdminInDB = Depends(get_current_admin)):
    # Only admins can access this endpoint
    users = db.query(User).all()
    return users