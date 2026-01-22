from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User, ReferralInvite
from app.schemas import ReferralLink

router = APIRouter(prefix="/api/referrals", tags=["referrals"])
logger = logging.getLogger(__name__)


def _generate_unique_code(db: Session) -> str:
    for _ in range(5):
        code = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:16]
        existing = db.query(ReferralInvite).filter(ReferralInvite.code == code).first()
        if not existing:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate referral code"
    )


@router.post("/create", response_model=ReferralLink)
async def create_referral_link(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or reuse a referral link for the current user"""
    try:
        existing = db.query(ReferralInvite).filter(
            ReferralInvite.inviter_id == current_user.id,
            ReferralInvite.is_active == True,
            ReferralInvite.claimed_by_user_id == None
        ).order_by(ReferralInvite.created_at.desc()).first()

        invite = existing
        if not invite:
            code = _generate_unique_code(db)
            invite = ReferralInvite(
                inviter_id=current_user.id,
                code=code,
                reward_amount=500.0
            )
            db.add(invite)
            db.commit()
            db.refresh(invite)

        base_url = str(request.base_url).rstrip("/")
        link = f"{base_url}/?ref={invite.code}"

        return ReferralLink(
            code=invite.code,
            url=link,
            reward_amount=invite.reward_amount,
            clicks=invite.clicks,
            created_at=invite.created_at,
            claimed=invite.claimed_by_user_id is not None
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
    """Track referral link clicks"""
    try:
        invite = db.query(ReferralInvite).filter(
            ReferralInvite.code == code,
            ReferralInvite.is_active == True
        ).first()

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referral code not found"
            )

        invite.clicks += 1
        invite.last_clicked_at = datetime.utcnow()
        db.commit()

        return {"status": "tracked"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error tracking referral click")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track referral"
        )
