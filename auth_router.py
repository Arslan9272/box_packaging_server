from fastapi import APIRouter, HTTPException, status, Depends,Body
from fastapi.security import OAuth2PasswordBearer
from schema import UserSchema,LoginModel
from database import SessionLocal
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from jose import jwt, JWTError  
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):  
    payload = verify_token(token)
    email = payload.get("sub")
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@auth_router.post("/signup", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def signup(user: UserSchema, db=Depends(get_db)):
   
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    db_username = db.query(User).filter(User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    new_user = User(
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
async def login(form_data: LoginModel = Body(...), db=Depends(get_db)):
    
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not check_password_hash(user.password, form_data.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/profile")
async def profile(current_user: User = Depends(get_current_user)):
    
    return {
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }