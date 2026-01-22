from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from app.database import get_db
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.models import User, ReferralInvite
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

def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register new user"""
    try:
        client_ip = get_client_ip(request)
        device_id = request.cookies.get("device_id")
        if not device_id:
            import uuid
            device_id = uuid.uuid4().hex

        # Check if user exists
        existing_user = db.query(User).filter(
            User.username == user_data.username
        ).first()
        
        if existing_user:
            log_error(
                f"Registration failed: User already exists",
                "DUPLICATE_USER",
                context={'username': user_data.username}
            )

        # Enforce single account per device/IP
        if client_ip:
            ip_user = db.query(User).filter(User.registration_ip == client_ip).first()
            if ip_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only one account can be registered per computer"
                )

        device_user = db.query(User).filter(User.registration_device_id == device_id).first()
        if device_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only one account can be registered per computer"
            )

        referral_invite = None
        if user_data.referral_code:
            referral_invite = db.query(ReferralInvite).filter(
                ReferralInvite.code == user_data.referral_code,
                ReferralInvite.is_active == True,
                ReferralInvite.claimed_by_user_id == None
            ).first()

            if not referral_invite:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or already used referral code"
                )

            if referral_invite.clicks < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referral link must be clicked before registration"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)

        new_user = User(
            username=user_data.username,
            password_hash=hashed_password,
            balance=1000.0,  # Starting balance
            registration_ip=client_ip,
            registration_device_id=device_id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        if referral_invite:
            inviter = db.query(User).filter(User.id == referral_invite.inviter_id).first()
            if inviter:
                inviter.balance += referral_invite.reward_amount
                inviter.total_won += referral_invite.reward_amount
            referral_invite.claimed_by_user_id = new_user.id
            referral_invite.claimed_at = datetime.utcnow()
            referral_invite.is_active = False
            db.commit()
        
        # Create token
        access_token = create_access_token(data={"sub": new_user.username})
        
        log_user_action("user_registration", new_user.id)
        
        response.set_cookie(
            key="device_id",
            value=device_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 365
        )

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
