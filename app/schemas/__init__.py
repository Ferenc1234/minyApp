from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    referral_code: Optional[str] = Field(default=None, max_length=32)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    balance: float
    total_wagered: float
    total_won: float
    total_games: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class UserProfile(UserResponse):
    pass

# Game Schemas
class GameCreate(BaseModel):
    bet_amount: float = Field(..., gt=0, le=10000)
    grid_size: int = Field(..., ge=3, le=5)  # 3, 4, or 5
    mines_count: int = Field(..., ge=1)

class CellClick(BaseModel):
    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)

class GameState(BaseModel):
    id: int
    user_id: int
    bet_amount: float
    grid_size: int
    mines_count: int
    status: str
    current_multiplier: float
    prize_amount: float
    revealed_cells: Dict[str, bool]
    grid: List[List[int]] = []  # Send grid only if still playing
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GameResult(BaseModel):
    game_id: int
    status: str
    prize_amount: float
    message: str

class GameHistory(BaseModel):
    id: int
    bet_amount: float
    grid_size: int
    mines_count: int
    status: str
    prize_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Statistics Schemas
class UserStats(BaseModel):
    rank: int
    username: str
    total_games: int
    total_wagered: float
    total_won: float
    win_rate: float
    balance: float
    created_at: datetime

class Leaderboard(BaseModel):
    users: List[UserStats]
    total_users: int

# Auth Response
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

class ReferralLink(BaseModel):
    code: str
    url: str
    reward_amount: float
    clicks: int
    created_at: datetime
    claimed: bool
