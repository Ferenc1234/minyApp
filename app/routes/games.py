from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from datetime import datetime
from app.database import get_db
from app.schemas import GameCreate, CellClick, GameState, GameResult, GameHistory
from app.models import User, Game, GameStatus
from app.routes.auth import get_current_user
from app.utils import GameEngine
from app.utils.logger import log_game_action, log_error
import logging

router = APIRouter(prefix="/api/games", tags=["games"])
logger = logging.getLogger(__name__)

@router.post("/new", response_model=GameState)
async def create_new_game(
    game_data: GameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new mine game"""
    try:
        # Validate game parameters
        if not GameEngine.validate_game_params(game_data.grid_size, game_data.mines_count):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid grid size or mines count"
            )
        
        # Check if user has enough balance
        if current_user.balance < game_data.bet_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance for this bet"
            )
        
        # Create mine field
        grid, grid_dict = GameEngine.create_minefield(game_data.grid_size, game_data.mines_count)
        
        # Create game record
        new_game = Game(
            user_id=current_user.id,
            bet_amount=game_data.bet_amount,
            grid_size=game_data.grid_size,
            mines_count=game_data.mines_count,
            grid_state=json.dumps(grid_dict),
            revealed_cells={},
            current_multiplier=1.0,
            status=GameStatus.ACTIVE,
            prize_amount=game_data.bet_amount
        )
        
        db.add(new_game)
        db.commit()
        db.refresh(new_game)
        
        # Update user stats
        current_user.total_games += 1
        current_user.total_wagered += game_data.bet_amount
        current_user.balance -= game_data.bet_amount
        db.commit()
        
        log_game_action(
            "game_started",
            current_user.id,
            new_game.id,
            {
                'bet_amount': game_data.bet_amount,
                'grid_size': game_data.grid_size,
                'mines_count': game_data.mines_count
            }
        )
        
        return GameState.model_validate(new_game)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating game")
        log_error(str(e), "GAME_CREATION_ERROR", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create game"
        )

@router.post("/{game_id}/click", response_model=GameResult)
async def click_cell(
    game_id: int,
    click_data: CellClick,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Click on a mine field cell"""
    try:
        # Get game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        # Check ownership
        if game.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your game"
            )
        
        # Check game status
        if game.status != GameStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Game is {game.status}"
            )
        
        # Process click
        result = GameEngine.process_click(game, click_data.row, click_data.col)
        
        if result.get('error'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        # Update game
        db.commit()
        db.refresh(game)
        
        log_game_action(
            "cell_clicked",
            current_user.id,
            game_id,
            {
                'row': click_data.row,
                'col': click_data.col,
                'hit_mine': result['hit_mine'],
                'multiplier': result['multiplier']
            }
        )
        
        return GameResult(
            game_id=game_id,
            status=game.status,
            prize_amount=game.prize_amount,
            message=result['message']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing click")
        log_error(str(e), "CLICK_ERROR", current_user.id, {'game_id': game_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process click"
        )

@router.post("/{game_id}/claim", response_model=GameResult)
async def claim_prize(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Claim prize and end game"""
    try:
        # Get game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        # Check ownership
        if game.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your game"
            )
        
        # Check game status
        if game.status != GameStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Game is already {game.status}"
            )
        
        # Claim prize
        game.status = GameStatus.CLAIMED
        
        # Update user balance and stats
        current_user.balance += game.prize_amount
        current_user.total_won += game.prize_amount
        
        db.commit()
        db.refresh(game)
        
        log_game_action(
            "prize_claimed",
            current_user.id,
            game_id,
            {
                'prize_amount': game.prize_amount,
                'multiplier': game.current_multiplier
            }
        )
        
        return GameResult(
            game_id=game_id,
            status=game.status,
            prize_amount=game.prize_amount,
            message=f"Prize claimed! Won ${game.prize_amount:.2f}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error claiming prize")
        log_error(str(e), "CLAIM_ERROR", current_user.id, {'game_id': game_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim prize"
        )

@router.get("/{game_id}", response_model=GameState)
async def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get game state"""
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        if game.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your game"
            )
        
        return GameState.model_validate(game)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting game")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get game"
        )

@router.get("/user/history", response_model=list[GameHistory])
async def get_game_history(
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
        logger.exception("Error getting game history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get game history"
        )
