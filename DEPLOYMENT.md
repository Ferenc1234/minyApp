# Mine Gambling Game - Deployment Guide

## Project Overview

A full-stack gambling mine game application with:
- **Backend**: FastAPI + PostgreSQL
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Database**: 2 tables (Users, Games)
- **Authentication**: JWT-based with bcrypt password hashing
- **Logging**: Safe logging system with sensitive data sanitization
- **Multi-user Support**: Real-time support for multiple concurrent players
- **Leaderboard**: Global ranking and statistics
- **Docker**: Containerized with Docker Compose
- **Kubernetes**: Production-ready K8s manifests

## Quick Start

### Local Development

```bash
# 1. Clone and enter directory
cd /home/student/Rubacek/minyApp

# 2. Install dependencies
make install

# 3. Start PostgreSQL and app with Docker Compose
make up

# 4. Access the app
# Open browser: http://localhost:8000

# 5. View logs
make logs

# 6. Stop services
make down
```

### Using Docker Only

```bash
# Build image
docker build -t mine-app:latest .

# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## Production Deployment

### Docker Compose (Production)

```bash
# Set environment variables
export SECRET_KEY="your-production-secret-key-here"

# Start production stack (with NGINX)
make prod-up

# Access via http://localhost:80

# Stop
make prod-down
```

### Kubernetes Deployment

```bash
# 1. Build and push image
docker build -t your-registry/mine-app:latest .
docker push your-registry/mine-app:latest

# 2. Update image in kubernetes/app-deployment.yaml if needed

# 3. Deploy to cluster
chmod +x kubernetes/deploy.sh
./kubernetes/deploy.sh

# 4. Verify deployment
kubectl get pods
kubectl get svc mine-app

# 5. Access application
kubectl port-forward svc/mine-app 8000:80
# Open browser: http://localhost:8000

# 6. View logs
kubectl logs -f deployment/mine-app

# 7. Cleanup
./kubernetes/undeploy.sh
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Bcrypt hashed password
- `balance`: Current player balance (starts at $1000)
- `total_wagered`: Total amount wagered
- `total_won`: Total amount won
- `total_games`: Game count
- `created_at`: Registration timestamp
- `updated_at`: Last update timestamp
- `is_active`: Account status

### Games Table
- `id`: Primary key
- `user_id`: Foreign key to Users
- `bet_amount`: Amount wagered
- `grid_size`: Grid size (3, 4, or 5)
- `mines_count`: Number of mines
- `grid_state`: JSON mine field configuration
- `revealed_cells`: JSON of revealed cells
- `current_multiplier`: Current reward multiplier
- `status`: Game status (active, won, lost, claimed)
- `prize_amount`: Final prize amount
- `created_at`: Game start time
- `updated_at`: Last update time

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout

### Games
- `POST /api/games/new` - Create new game
- `POST /api/games/{id}/click` - Click cell in mine field
- `POST /api/games/{id}/claim` - Claim prize
- `GET /api/games/{id}` - Get game state
- `GET /api/games/user/history` - Get game history

### User
- `GET /api/user/profile` - Get user profile
- `GET /api/user/history` - Get detailed game history
- `GET /api/user/stats` - Get user statistics
- `GET /api/user/leaderboard` - Get global leaderboard

### System
- `GET /health` - Health check
- `GET /api/status` - API status

## Game Rules

1. **Bet Selection**: Player chooses bet amount ($1-$10,000)
2. **Grid Setup**: Select grid size (3x3, 4x4, 5x5) and mines count
3. **Gameplay**: Click safe cells to increase multiplier
4. **Win/Loss**:
   - Click mine: Game ends, lose entire bet
   - Click safe cell: Multiplier increases, can claim prize anytime
   - Claim prize: Lock in current multiplier × bet amount
5. **Reward Calculation**: Multiplier based on grid difficulty and safe clicks

## Configuration

### Environment Variables

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://mineuser:minepass@localhost:5432/minedb

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
SQLALCHEMY_ECHO=False
```

### Docker Compose Override

Edit `docker-compose.yml` to customize:
- Database credentials
- Port mappings
- Volume mounts
- Environment variables

## Monitoring & Logs

### Local Logs
```bash
# View container logs
docker-compose logs -f app
docker-compose logs -f db

# View application logs
tail -f logs/app.log
```

### Kubernetes Logs
```bash
# View pod logs
kubectl logs deployment/mine-app
kubectl logs -f deployment/mine-app --all-containers=true

# View previous logs (if pod crashed)
kubectl logs deployment/mine-app --previous

# Stream logs from multiple pods
kubectl logs -f deployment/mine-app --all-containers=true --tail=50
```

## Scaling

### Docker Compose
Limited to single machine, increase resources via Docker daemon settings.

### Kubernetes
Horizontal Pod Autoscaler automatically scales between 2-10 replicas based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

Manual scaling:
```bash
kubectl scale deployment mine-app --replicas=5
```

## Backup & Recovery

### Database Backup
```bash
# Docker
docker-compose exec db pg_dump -U mineuser minedb > backup.sql

# Kubernetes
kubectl exec deployment/mine-postgres -- pg_dump -U mineuser minedb > backup.sql
```

### Database Restore
```bash
# Docker
docker-compose exec -i db psql -U mineuser minedb < backup.sql

# Kubernetes
kubectl exec -i deployment/mine-postgres -- psql -U mineuser minedb < backup.sql
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>

# Or use different port
docker-compose -f docker-compose.yml up -p 8001:8000
```

### Database Connection Error
```bash
# Check if DB is running
docker-compose ps

# Check DB logs
docker-compose logs db

# Restart DB
docker-compose restart db
```

### Application Crashes
```bash
# Check logs
docker-compose logs app

# Rebuild image
docker-compose build --no-cache
docker-compose restart app
```

### Permission Denied Errors
```bash
# Ensure correct permissions
chmod +x kubernetes/deploy.sh kubernetes/undeploy.sh
```

## Performance Optimization

1. **Caching**: Frontend caches static assets
2. **Gzip Compression**: NGINX compresses responses
3. **Database Indexing**: Indexes on frequently queried columns
4. **Connection Pooling**: SQLAlchemy pool configured
5. **Load Balancing**: Kubernetes service distributes traffic
6. **Auto-scaling**: HPA handles traffic spikes

## Security Considerations

1. **Passwords**: Bcrypt hashing with salt
2. **API Authentication**: JWT tokens with expiration
3. **Input Validation**: Pydantic schemas validate all inputs
4. **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries
5. **CORS**: Configured for frontend domain
6. **Logging**: Sensitive data automatically redacted
7. **HTTPS**: Use NGINX reverse proxy with SSL
8. **Database**: Credentials in secrets, not in code

## Advanced Configuration

### NGINX with SSL
```bash
# Update nginx.conf with SSL configuration
# Place certificate and key files
# Restart NGINX container
```

### Database Replication
For high availability:
```bash
# Use PostgreSQL streaming replication
# Configure standby replicas
# Update Kubernetes StatefulSet
```

### Distributed Tracing
Integration with Jaeger or similar:
```bash
# Add OpenTelemetry instrumentation
# Configure collector endpoint
```

## Support & Maintenance

- Review logs regularly for errors
- Monitor database size and performance
- Update dependencies periodically
- Test backup/restore procedures
- Review security patches
- Monitor resource usage and scale as needed

## Project Structure

```
minyApp/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── schemas/         # Pydantic schemas
│   ├── utils/           # Utilities (auth, game logic, logging)
│   └── database.py      # Database configuration
├── kubernetes/          # K8s manifests
├── static/              # Frontend assets
├── templates/           # HTML templates
├── main.py             # FastAPI app entry
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Development stack
├── docker-compose.prod.yml  # Production stack
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── Makefile            # Helper commands
```
