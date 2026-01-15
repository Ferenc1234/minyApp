from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.models import User
from app.utils import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    verify_token,
    authenticate_user
)
from app.utils.logger import log_user_action, log_error
import logging

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
security = HTTPBearer()

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            log_error(
                f"Registration failed: User already exists",
                "DUPLICATE_USER",
                context={'username': user_data.username}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            balance=1000.0  # Starting balance
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create token
        access_token = create_access_token(data={"sub": new_user.username})
        
        log_user_action("user_registration", new_user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(new_user)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during registration")
        log_error(str(e), "REGISTRATION_ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        user = authenticate_user(db, credentials.username, credentials.password)
        
        if not user:
            log_error(
                f"Login failed for user",
                "INVALID_CREDENTIALS",
                context={'username': credentials.username}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create token
        access_token = create_access_token(data={"sub": user.username})
        
        log_user_action("user_login", user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during login")
        log_error(str(e), "LOGIN_ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    username = verify_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (token invalidation happens client-side)"""
    log_user_action("user_logout", current_user.id)
    return {"message": "Logged out successfully"}
