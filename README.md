# Mine Gambling Game

A Python-based gambling mine game application with user authentication, database persistence, multi-user support, and statistics tracking.

## Features

- User registration and authentication (JWT-based)
- Secure password hashing with bcrypt
- Mine sweeper-style gambling game with configurable grid size and mines
- Dynamic reward calculation based on grid difficulty
- Real-time balance management
- Multi-user support with individual game states
- Leaderboard and user statistics
- Safe logging of all activities
- Docker Compose setup for easy deployment
- Kubernetes support

## Project Structure

```
minyApp/
├── app/
│   ├── models/          # SQLAlchemy database models
│   ├── routes/          # API endpoints
│   ├── schemas/         # Pydantic request/response schemas
│   ├── utils/           # Utility functions (auth, game logic, logging)
│   └── __init__.py
├── static/              # Frontend CSS, JS
├── templates/           # HTML templates
├── migrations/          # Alembic database migrations
├── kubernetes/          # Kubernetes deployment files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py              # Application entry point
```

## Installation

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure
6. Run database migrations: `alembic upgrade head`
7. Start the application: `python main.py`

### Docker Compose

```bash
docker-compose up -d
```

This will start:
- FastAPI application on http://localhost:8000
- PostgreSQL database on localhost:5432

### Kubernetes

```bash
kubectl apply -f kubernetes/
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user

### Game
- `POST /api/games/new` - Start new game (bet_amount, grid_size, mines_count)
- `POST /api/games/{game_id}/click` - Click on cell (row, col)
- `POST /api/games/{game_id}/claim` - Claim prize
- `GET /api/games/{game_id}` - Get game state

### User
- `GET /api/user/profile` - Get user profile
- `GET /api/user/history` - Get user game history
- `GET /api/leaderboard` - Get global leaderboard

## Game Rules

1. User selects bet amount, grid size, and number of mines
2. Grid is randomly generated with mines placed
3. User clicks cells to reveal them (safe cells give reward multiplier)
4. User can claim current reward at any time
5. If user clicks mine, game ends and bet is lost
6. Reward multiplier increases with each safe click
