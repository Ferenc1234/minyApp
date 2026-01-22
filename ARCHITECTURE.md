# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                            │
├─────────────────────────────────────────────────────────────┤
│  HTML/CSS/JavaScript (Single Page App)                      │
│  - Frontend state management                                │
│  - JWT token storage                                        │
│  - WebSocket/Fetch API communication                        │
└────────────────────────────────┬────────────────────────────┘
                                 │ HTTP/HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  NGINX Reverse Proxy                        │
├─────────────────────────────────────────────────────────────┤
│  - SSL/TLS termination                                      │
│  - Gzip compression                                         │
│  - Static file serving                                      │
│  - Load balancing (in K8s)                                  │
└────────────────────────────────┬────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application (Multi-instance)           │
├─────────────────────────────────────────────────────────────┤
│  app/                                                       │
│  ├── routes/auth.py      → Authentication endpoints        │
│  ├── routes/games.py     → Game management endpoints       │
│  ├── routes/users.py     → User & leaderboard endpoints    │
│  ├── models/             → Database models (SQLAlchemy)    │
│  ├── schemas/            → Request/response validation     │
│  ├── utils/              → Business logic                  │
│  │   ├── auth.py         → JWT & password hashing          │
│  │   ├── game_engine.py  → Mine field & reward calc        │
│  │   └── logger.py       → Secure logging                  │
│  └── database.py         → ORM & connection pool           │
└────────────────────────────────┬────────────────────────────┘
                                 │ SQL (psycopg2)
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                            │
├─────────────────────────────────────────────────────────────┤
│  users                          games                       │
│  ├── id (PK)                   ├── id (PK)                 │
│  ├── username (UNIQUE)         ├── user_id (FK)            │
│  ├── password_hash             ├── bet_amount              │
│  ├── balance                   ├── grid_size               │
│  ├── total_wagered             ├── mines_count             │
│  ├── total_won                 ├── grid_state (JSON)       │
│  ├── total_games               ├── revealed_cells (JSON)   │
│  ├── created_at                ├── current_multiplier      │
│  ├── updated_at                ├── status (ENUM)           │
│  └── is_active                 ├── prize_amount            │
│                                ├── created_at              │
│                                ├── updated_at              │
│                                └── Indexes on user_id      │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend Layer

**Technology**: HTML5, CSS3, Vanilla JavaScript

**Responsibilities**:
- User interface rendering
- Form validation and submission
- State management (game, user, auth)
- Real-time UI updates
- Token management (localStorage)
- API communication (Fetch API)

**Key Files**:
- `templates/index.html` - Main application template
- `static/style.css` - Application styling
- `static/app.js` - Frontend logic

### Backend Layer

**Technology**: FastAPI + Python 3.11

**Responsibilities**:
- Request routing
- Authentication & authorization
- Business logic implementation
- Database operations
- Input validation
- Error handling
- Logging

**Components**:

#### Routes (`app/routes/`)
- **auth.py**: Registration, login, logout endpoints
- **games.py**: Game CRUD, cell clicks, prize claiming
- **users.py**: User profile, statistics, leaderboard

#### Models (`app/models/`)
- **User**: Player account data
- **Game**: Game state and results

#### Schemas (`app/schemas/`)
- Request validation (Pydantic)
- Response serialization
- Type hints

#### Utils (`app/utils/`)
- **auth.py**: Password hashing, JWT tokens
- **game_engine.py**: Mine field generation, logic
- **logger.py**: Safe, structured logging

### Data Layer

**Technology**: PostgreSQL + SQLAlchemy ORM

**Two-Table Design**:

1. **Users Table**
   - Stores player accounts
   - Balance tracking
   - Statistics aggregation
   - Soft deletion support (is_active)

2. **Games Table**
   - Game instances
   - Mine field configuration (JSON)
   - Game state (JSON)
   - Results and prizes

## Data Flow

### Registration Flow
```
User Input (HTML Form)
    ↓
Frontend Validation
    ↓
POST /api/auth/register
    ↓
Backend Validation (Pydantic)
    ↓
Duplicate Check (Query DB)
    ↓
Password Hashing (bcrypt)
    ↓
Create User Record
    ↓
Generate JWT Token
    ↓
Return Token + User Data
    ↓
Store Token (localStorage)
    ↓
Redirect to Game Screen
```

### Game Flow
```
User Chooses Game Params
    ↓
POST /api/games/new
    ↓
Validate Bet vs Balance
    ↓
Generate Mine Field
    ↓
Create Game Record
    ↓
Deduct Bet from Balance
    ↓
Return Game State (Grid hidden)
    ↓
Display Mine Field UI
    ↓
    ├─→ User Clicks Cell
    │   ├─→ POST /api/games/{id}/click
    │   ├─→ Validate Click
    │   ├─→ Check for Mine
    │   ├─→ Update Multiplier
    │   ├─→ Update Prize Amount
    │   ├─→ Save Game State
    │   ├─→ Return Result
    │   └─→ Update UI
    │
    └─→ User Claims Prize
        ├─→ POST /api/games/{id}/claim
        ├─→ Lock in Prize
        ├─→ Add to Balance
        ├─→ Update Stats
        ├─→ Save Game Result
        └─→ Show Result Screen
```

## Security Architecture

### Authentication
- **JWT Tokens**: Stateless, expiring tokens
- **Password Hashing**: Bcrypt with salt
- **Token Validation**: On every protected endpoint

### Data Protection
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS**: Configured for frontend domain
- **HTTPS Ready**: NGINX SSL support

### Logging Security
- **No Sensitive Data**: Passwords/tokens filtered
- **Structured Logging**: JSON format
- **Log Rotation**: Prevent disk overflow
- **Access Logs**: Separate from application logs

## Deployment Architecture

### Development
```
Docker Container (App)  ←→  Docker Container (PostgreSQL)
         ↓
    localhost:8000
```

### Production (Docker Compose)
```
┌─────────────────────┐
│   NGINX Container   │
│   Port 80/443       │
└──────────────┬──────┘
               │
    ┌──────────┼──────────┐
    ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐
│ App 1  │ │ App 2  │ │ App 3  │
└────────┘ └────────┘ └────────┘
    │          │          │
    └──────────┼──────────┘
               ↓
        ┌─────────────┐
        │ PostgreSQL  │
        └─────────────┘
```

### Production (Kubernetes)
```
┌──────────────────────────────────────────────┐
│         Kubernetes Cluster                   │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │ Service (LoadBalancer/NodePort)     │   │
│  │ Port 80 → Pod 8000                  │   │
│  └────────────┬────────────────────────┘   │
│               │                            │
│   ┌───────────┼───────────────────┐       │
│   │           │                   │       │
│  Pod 1      Pod 2               Pod 3     │
│  App        App                 App       │
│  ↓          ↓                    ↓        │
│  └───────────┼────────────────────┘       │
│              │                            │
│   ┌──────────┴────────────┐              │
│   ↓                       ↓              │
│  PVC                   PostgreSQL Pod    │
│  (Persistent Volume)                     │
│  (Data Storage)                          │
│                                          │
│  HPA: Auto-scales 2-10 replicas         │
│       based on CPU/Memory               │
└──────────────────────────────────────────┘
```

## Scaling Strategy

### Horizontal Scaling
- **Stateless Design**: Each app instance is independent
- **Shared Database**: PostgreSQL handles concurrency
- **Load Balancing**: Kubernetes service distributes traffic
- **Auto-scaling**: HPA adjusts replicas based on metrics

### Database Scaling
- **Connection Pooling**: SQLAlchemy manages connections
- **Prepared Statements**: Reusable query plans
- **Indexing**: On user_id and frequently queried columns
- **Future**: Read replicas for read-heavy workloads

## Performance Considerations

### Caching
- **Frontend Caching**: Static assets cached by browser
- **GZIP Compression**: Reduces response size
- **Database Queries**: Indexed for fast lookups

### Optimization
- **ORM Eager Loading**: Prevent N+1 queries
- **Connection Pooling**: Reuse DB connections
- **Async I/O**: Non-blocking in FastAPI
- **Response Serialization**: Pydantic models

## Monitoring & Observability

### Logs
- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Rotation**: Max 10MB, 5 backups
- **Sanitization**: No sensitive data

### Metrics (Future)
- Request count and latency
- Database query performance
- Resource utilization (CPU, Memory)
- Error rates and exceptions
- User activity metrics

### Health Checks
- `/health` endpoint (basic)
- Liveness probe (Kubernetes)
- Readiness probe (Kubernetes)
- Database connectivity check

## Error Handling

### API Responses
```json
{
  "status_code": 400,
  "detail": "User already registered"
}
```

### Client-side
- Display user-friendly messages
- Log errors for debugging
- Automatic retry on network errors
- Graceful degradation

### Server-side
- Try/catch blocks around operations
- Validate all inputs
- Return appropriate HTTP status codes
- Log stack traces for debugging

## Future Enhancements

1. **WebSocket Support**: Real-time multiplayer
2. **Caching Layer**: Redis for sessions
3. **Message Queue**: Celery for async tasks
4. **Analytics**: User behavior tracking
5. **Payment Integration**: Real money betting
6. **Mobile App**: Native iOS/Android
7. **AI Opponent**: Computer player
8. **Tournaments**: Multi-player competitions
