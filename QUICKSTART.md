# Mine Gambling Game - Quick Start Guide

## ⚡ 5-Minute Setup

### Prerequisites
- Docker & Docker Compose (or Python 3.11+)
- Git (optional)

### Option 1: Docker Compose (Recommended)

```bash
# 1. Enter directory
cd /home/student/Rubacek/minyApp

# 2. Start services
docker compose up -d

# 3. Wait for database to initialize (10-15 seconds)
sleep 10

# 4. Open browser
# http://localhost:8000

# 5. Create account and play!
```

**Stop services:**
```bash
docker-compose down
```

---

### Option 2: Local Python Development

```bash
# 1. Enter directory
cd /home/student/Rubacek/minyApp

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start database (requires Docker)
docker-compose up -d db

# 5. Initialize database
python -c "from app.database import init_db; init_db()"

# 6. Run application
python main.py

# 7. Open http://localhost:8000
```

---

## 🎮 How to Play

1. **Register/Login**
   - Create account with username, email, password
   - Login with credentials

2. **Start Game**
   - Choose bet amount ($1-$10,000)
   - Select grid size (3x3, 4x4, 5x5)
   - Choose number of mines
   - Click "Start Game"

3. **Gameplay**
   - Click on grid cells to reveal them
   - Safe cells = increase multiplier
   - Mine = game ends, lose bet
   - Watch your multiplier grow
   - Click "Claim Prize" to lock in winnings

4. **Win/Lose**
   - **Win**: Claim before hitting mine
   - **Lose**: Click mine and lose bet
   - **Statistics**: View your performance

---

## 📊 API Quick Reference

Access interactive docs: **http://localhost:8000/docs**

### Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"pass123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass123"}'
```

### Create Game
```bash
TOKEN="your_token_from_login"
curl -X POST http://localhost:8000/api/games/new \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bet_amount":100,"grid_size":3,"mines_count":2}'
```

---

## 📁 Project Structure

```
minyApp/
├── app/                      # Application code
│   ├── models/              # Database models
│   ├── routes/              # API endpoints
│   ├── schemas/             # Request/response schemas
│   ├── utils/               # Authentication, game logic, logging
│   └── database.py          # Database config
├── static/                   # Frontend (CSS, JavaScript)
├── templates/                # HTML files
├── kubernetes/               # Kubernetes manifests
├── main.py                   # FastAPI application
├── Dockerfile                # Container image
├── docker-compose.yml        # Development stack
├── requirements.txt          # Python dependencies
├── README.md                 # Full documentation
├── DEPLOYMENT.md             # Deployment guide
├── TESTING.md                # Testing guide
└── Makefile                  # Helper commands
```

---

## 🛠️ Useful Commands

```bash
# View logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Remove all data and start fresh
docker-compose down -v

# Connect to database
docker-compose exec db psql -U mineuser -d minedb

# Rebuild image
docker-compose build --no-cache

# Restart specific service
docker-compose restart app
```

---

## 🚀 Production Deployment

### Docker Compose (with NGINX)
```bash
docker-compose -f docker-compose.prod.yml up -d
# Access at http://localhost:80
```

### Kubernetes
```bash
./kubernetes/deploy.sh
# Access with: kubectl port-forward svc/mine-app 8000:80
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 🐛 Troubleshooting

### Port 8000 already in use
```bash
# Find process
lsof -i :8000
# Kill it
kill -9 <PID>
```

### Database connection error
```bash
# Restart database
docker-compose restart db
# Wait 10 seconds for it to initialize
```

### Permission denied
```bash
# Make scripts executable
chmod +x kubernetes/deploy.sh run.sh
```

### Application won't start
```bash
# Check logs
docker-compose logs app

# Rebuild image
docker-compose build --no-cache
docker-compose restart app
```

---

## 📚 Documentation

- **[README.md](README.md)** - Project overview
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[TESTING.md](TESTING.md)** - Testing procedures
- **[kubernetes/README.md](kubernetes/README.md)** - Kubernetes setup

---

## 🔐 Features

✅ User registration & authentication (JWT)  
✅ Secure password hashing (bcrypt)  
✅ Multi-user concurrent play  
✅ Real-time game state  
✅ Dynamic reward calculation  
✅ Global leaderboard  
✅ User statistics  
✅ Safe logging (no sensitive data)  
✅ PostgreSQL database  
✅ Docker containerization  
✅ Kubernetes ready  
✅ NGINX reverse proxy  
✅ Auto-scaling support  

---

## 💡 Tips

1. **Start with small bets** to learn the game
2. **Claim early** - Higher multipliers are riskier
3. **Watch the leaderboard** - See how others perform
4. **Check statistics** - Track your ROI and win rate
5. **Use Docs** - http://localhost:8000/docs for API testing

---

## 📞 Support

For issues:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review logs: `docker-compose logs app`
3. Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup
4. Review [TESTING.md](TESTING.md) for testing procedures

---

**Enjoy the game! 🎉**
