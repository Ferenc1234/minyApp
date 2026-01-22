from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User
import logging

router = APIRouter(prefix="/api/casino", tags=["casino"])
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_casino_stats(db: Session = Depends(get_db)):
    """Return aggregate casino edge statistics.

    Casino profit is defined as the total amount wagered by all users
    minus the total amount paid out in winnings.
    """
    try:
        total_wagered = db.query(func.coalesce(func.sum(User.total_wagered), 0.0)).scalar() or 0.0
        total_won = db.query(func.coalesce(func.sum(User.total_won), 0.0)).scalar() or 0.0
        casino_profit = total_wagered - total_won
        edge_pct = (casino_profit / total_wagered * 100.0) if total_wagered > 0 else 0.0

        return {
            "total_wagered": round(total_wagered, 2),
            "total_won": round(total_won, 2),
            "casino_profit": round(casino_profit, 2),
            "casino_edge_percent": round(edge_pct, 2),
        }
    except Exception:
        logger.exception("Error computing casino stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute casino statistics",
        )
