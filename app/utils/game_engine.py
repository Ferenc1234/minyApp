import random
from typing import Dict, List, Tuple, Optional
from app.models import Game, GameStatus
import logging

logger = logging.getLogger(__name__)

class MineField:
    """Represents a mine field for the gambling game"""
    
    def __init__(self, grid_size: int, mines_count: int):
        self.grid_size = grid_size
        self.mines_count = mines_count
        self.grid = self._generate_grid()
        self.revealed = set()
        
    def _generate_grid(self) -> List[List[int]]:
        """Generate a grid with mines randomly placed"""
        # Create empty grid
        grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Place mines randomly
        total_cells = self.grid_size * self.grid_size
        if self.mines_count >= total_cells:
            raise ValueError("Mines count must be less than total cells")
        
        mine_positions = random.sample(range(total_cells), self.mines_count)
        for pos in mine_positions:
            row = pos // self.grid_size
            col = pos % self.grid_size
            grid[row][col] = 1  # 1 = mine
        
        return grid
    
    def is_mine(self, row: int, col: int) -> bool:
        """Check if cell contains a mine"""
        if not self._is_valid_cell(row, col):
            return False
        return self.grid[row][col] == 1
    
    def is_revealed(self, row: int, col: int) -> bool:
        """Check if cell was already revealed"""
        return (row, col) in self.revealed
    
    def reveal_cell(self, row: int, col: int) -> bool:
        """
        Reveal a cell. Returns True if it's a mine, False if safe.
        """
        if not self._is_valid_cell(row, col):
            raise ValueError(f"Invalid cell position: ({row}, {col})")
        
        if self.is_revealed(row, col):
            raise ValueError(f"Cell already revealed: ({row}, {col})")
        
        self.revealed.add((row, col))
        return self.is_mine(row, col)
    
    def get_revealed_cells(self) -> Dict[str, bool]:
        """Get dict of revealed cells"""
        return {f"{row},{col}": self.is_mine(row, col) for row, col in self.revealed}
    
    def get_safe_cells_count(self) -> int:
        """Get count of safe cells not yet revealed"""
        total_cells = self.grid_size * self.grid_size
        safe_cells = total_cells - self.mines_count
        revealed_safe = sum(1 for row, col in self.revealed if not self.is_mine(row, col))
        return safe_cells - revealed_safe
    
    def _is_valid_cell(self, row: int, col: int) -> bool:
        """Check if cell position is valid"""
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size

class GameEngine:
    """Handles game logic and reward calculations"""
    
    # Reward multipliers based on difficulty (grid_size and mines_count ratio)
    MULTIPLIER_BASE = {
        3: {1: 1.5, 2: 1.8, 3: 2.5},    # 3x3 grid
        4: {2: 1.3, 4: 1.6, 6: 2.0},    # 4x4 grid
        5: {3: 1.2, 5: 1.5, 8: 1.8}     # 5x5 grid
    }
    
    @staticmethod
    def create_minefield(grid_size: int, mines_count: int) -> Tuple[List[List[int]], Dict]:
        """Create new mine field and return grid and state"""
        field = MineField(grid_size, mines_count)
        grid_dict = {str(i): {str(j): field.grid[i][j] for j in range(grid_size)} 
                     for i in range(grid_size)}
        return field.grid, grid_dict
    
    @staticmethod
    def get_multiplier(grid_size: int, mines_count: int, safe_clicks: int) -> float:
        """Calculate current multiplier based on safe clicks"""
        base_multiplier = GameEngine.MULTIPLIER_BASE.get(grid_size, {}).get(mines_count, 1.0)
        
        # Increase multiplier slightly with each safe click
        multiplier = base_multiplier * (1 + (safe_clicks * 0.15))
        return round(multiplier, 2)
    
    @staticmethod
    def calculate_prize(bet_amount: float, multiplier: float) -> float:
        """Calculate prize amount"""
        return round(bet_amount * multiplier, 2)
    
    @staticmethod
    def validate_game_params(grid_size: int, mines_count: int) -> bool:
        """Validate game parameters"""
        total_cells = grid_size * grid_size
        
        # Check grid size
        if grid_size not in [3, 4, 5]:
            return False
        
        # Check mines count is reasonable
        if mines_count < 1 or mines_count >= total_cells:
            return False
        
        return True
    
    @staticmethod
    def process_click(game: Game, row: int, col: int) -> Dict:
        """
        Process a cell click and return game update
        Returns: {
            'hit_mine': bool,
            'safe_clicks': int,
            'multiplier': float,
            'prize_amount': float,
            'message': str
        }
        """
        import json
        
        # Validate cell position
        if not (0 <= row < game.grid_size and 0 <= col < game.grid_size):
            return {
                'hit_mine': False,
                'safe_clicks': 0,
                'multiplier': game.current_multiplier,
                'prize_amount': game.prize_amount,
                'message': 'Invalid cell position',
                'error': True
            }
        
        # Check if already revealed
        revealed_str = f"{row},{col}"
        if revealed_str in game.revealed_cells:
            return {
                'hit_mine': False,
                'safe_clicks': 0,
                'multiplier': game.current_multiplier,
                'prize_amount': game.prize_amount,
                'message': 'Cell already revealed',
                'error': True
            }
        
        # Check if hit mine
        grid = json.loads(game.grid_state) if isinstance(game.grid_state, str) else game.grid_state
        is_mine = bool(grid[str(row)].get(str(col), 0))
        
        # Update revealed cells
        revealed_cells = game.revealed_cells.copy() if isinstance(game.revealed_cells, dict) else {}
        revealed_cells[revealed_str] = is_mine
        game.revealed_cells = revealed_cells
        game.updated_at = __import__('datetime').datetime.utcnow()
        
        if is_mine:
            game.status = GameStatus.LOST
            game.prize_amount = 0
            return {
                'hit_mine': True,
                'safe_clicks': len([v for v in game.revealed_cells.values() if not v]),
                'multiplier': game.current_multiplier,
                'prize_amount': 0,
                'message': 'Hit a mine! Game over.'
            }
        else:
            # Safe click - update multiplier
            safe_clicks = len([v for v in game.revealed_cells.values() if not v])
            multiplier = GameEngine.get_multiplier(
                game.grid_size, 
                game.mines_count, 
                safe_clicks
            )
            prize = GameEngine.calculate_prize(game.bet_amount, multiplier)
            
            game.current_multiplier = multiplier
            game.prize_amount = prize
            
            return {
                'hit_mine': False,
                'safe_clicks': safe_clicks,
                'multiplier': multiplier,
                'prize_amount': prize,
                'message': f'Safe! Current multiplier: {multiplier}x, Prize: ${prize:.2f}'
            }
