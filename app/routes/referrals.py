from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User
from app.schemas import ReferralLink

router = APIRouter(prefix="/api/referrals", tags=["referrals"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=ReferralLink)
async def create_referral_link(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return a referral link for the current user (code = username)"""
    try:
        base_url = str(request.base_url).rstrip("/")
        link = f"{base_url}/?ref={current_user.username}"

        return ReferralLink(
            code=current_user.username,
            url=link,
            reward_amount=0.0,
            clicks=current_user.referral_count,
            created_at=current_user.created_at,
            claimed=False
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating referral link")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create referral link"
        )


@router.get("/track")
async def track_referral_click(code: str, db: Session = Depends(get_db)):
    """Track referral link clicks (no-op, code = username)"""
    try:
        user = db.query(User).filter(User.username == code).first()
        if user:
            return {"status": "tracked"}
        return {"status": "ignored"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error tracking referral click")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track referral"
        )
