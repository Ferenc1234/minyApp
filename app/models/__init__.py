from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class GameStatus(str, enum.Enum):
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    CLAIMED = "claimed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    balance = Column(Float, default=1000.0, nullable=False)
    total_wagered = Column(Float, default=0.0, nullable=False)
    total_won = Column(Float, default=0.0, nullable=False)
    total_games = Column(Integer, default=0, nullable=False)
    registration_ip = Column(String(45), index=True, nullable=True)
    registration_device_id = Column(String(64), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")
    referrals_sent = relationship(
        "ReferralInvite",
        back_populates="inviter",
        foreign_keys="ReferralInvite.inviter_id",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, balance={self.balance})>"

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bet_amount = Column(Float, nullable=False)
    grid_size = Column(Integer, nullable=False)  # 3, 4, or 5 (3x3, 4x4, 5x5)
    mines_count = Column(Integer, nullable=False)
    grid_state = Column(JSON, nullable=False)  # Store the mine field
    revealed_cells = Column(JSON, default={}, nullable=False)  # Store revealed cells: {(row,col): True/False}
    current_multiplier = Column(Float, default=1.0, nullable=False)
    status = Column(String(20), default=GameStatus.ACTIVE, nullable=False)
    prize_amount = Column(Float, default=0.0, nullable=False)  # Final prize if won/claimed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="games")
    
    def __repr__(self):
        return f"<Game(id={self.id}, user_id={self.user_id}, status={self.status}, prize={self.prize_amount})>"

class ReferralInvite(Base):
    __tablename__ = "referral_invites"

    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    reward_amount = Column(Float, default=500.0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    last_clicked_at = Column(DateTime, nullable=True)
    claimed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="referrals_sent")
    claimed_by = relationship("User", foreign_keys=[claimed_by_user_id])

    def __repr__(self):
        return f"<ReferralInvite(id={self.id}, inviter_id={self.inviter_id}, code={self.code}, claimed={self.claimed_by_user_id is not None})>"

__all__ = ['Base', 'User', 'Game', 'GameStatus', 'ReferralInvite']
