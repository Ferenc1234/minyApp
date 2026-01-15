from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.schemas import UserProfile, Leaderboard, UserStats, GameHistory
from app.models import User, Game, GameStatus
from app.routes.auth import get_current_user
import logging

router = APIRouter(prefix="/api/user", tags=["user"])
logger = logging.getLogger(__name__)

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    try:
        return UserProfile.model_validate(current_user)
    except Exception as e:
        logger.exception("Error getting profile")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.get("/history", response_model=list[GameHistory])
async def get_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's game history"""
    try:
        games = db.query(Game).filter(
            Game.user_id == current_user.id
        ).order_by(Game.created_at.desc()).offset(skip).limit(limit).all()
        
        return [GameHistory.model_validate(game) for game in games]
    except Exception as e:
        logger.exception("Error getting history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get history"
        )

@router.get("/leaderboard", response_model=Leaderboard)
async def get_leaderboard(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get global leaderboard"""
    try:
        users = db.query(User).filter(User.is_active == True).order_by(
            desc(User.total_won)
        ).limit(limit).all()
        
        user_stats = []
        for rank, user in enumerate(users, 1):
            win_rate = (user.total_won / user.total_wagered * 100) if user.total_wagered > 0 else 0
            stats = UserStats(
                rank=rank,
                username=user.username,
                total_games=user.total_games,
                total_wagered=user.total_wagered,
                total_won=user.total_won,
                win_rate=round(win_rate, 2),
                balance=user.balance,
                created_at=user.created_at
            )
            user_stats.append(stats)
        
        return Leaderboard(
            users=user_stats,
            total_users=len(users)
        )
    except Exception as e:
        logger.exception("Error getting leaderboard")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )

@router.get("/stats", response_model=dict)
async def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed user stats"""
    try:
        # Get user's games
        games = db.query(Game).filter(Game.user_id == current_user.id).all()
        
        won_games = len([g for g in games if g.status == GameStatus.CLAIMED])
        lost_games = len([g for g in games if g.status == GameStatus.LOST])
        
        win_rate = (won_games / current_user.total_games * 100) if current_user.total_games > 0 else 0
        roi = ((current_user.total_won - current_user.total_wagered) / current_user.total_wagered * 100) if current_user.total_wagered > 0 else 0
        
        return {
            "username": current_user.username,
            "balance": current_user.balance,
            "total_games": current_user.total_games,
            "won_games": won_games,
            "lost_games": lost_games,
            "total_wagered": current_user.total_wagered,
            "total_won": current_user.total_won,
            "win_rate": round(win_rate, 2),
            "roi": round(roi, 2),
            "joined": current_user.created_at
        }
    except Exception as e:
        logger.exception("Error getting stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stats"
        )
