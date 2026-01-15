# Mine Gambling Game - Testing Guide

## API Testing

### Using cURL

#### Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'
```

Response includes token:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {...}
}
```

#### Create Game
```bash
TOKEN="your_token_here"

curl -X POST http://localhost:8000/api/games/new \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "bet_amount": 100,
    "grid_size": 3,
    "mines_count": 2
  }'
```

#### Click Cell
```bash
curl -X POST http://localhost:8000/api/games/1/click \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "row": 0,
    "col": 0
  }'
```

#### Claim Prize
```bash
curl -X POST http://localhost:8000/api/games/1/claim \
  -H "Authorization: Bearer $TOKEN"
```

#### Get User Stats
```bash
curl http://localhost:8000/api/user/stats \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Leaderboard
```bash
curl http://localhost:8000/api/user/leaderboard \
  -H "Authorization: Bearer $TOKEN"
```

### Using Postman

1. Import the API endpoints into Postman
2. Create collection with folders:
   - Authentication
   - Games
   - User
3. Use environment variables for token and base URL
4. Test each endpoint with different payloads

### Using FastAPI Docs

Access interactive API documentation:
```
http://localhost:8000/docs
```

Features:
- Try out endpoints
- View schemas
- See response examples
- Auto-generated Swagger UI

## Manual Browser Testing

### Test Flow

1. **Registration**
   - Go to http://localhost:8000
   - Click "Register" tab
   - Fill in username, email, password
   - Should redirect to game screen

2. **Game Creation**
   - Enter bet amount: 100
   - Select grid size: 3x3
   - Enter mines: 2
   - Click "Start Game"

3. **Gameplay**
   - Click cells carefully
   - Watch multiplier increase
   - Click "Claim Prize" to win
   - Or click mine to lose

4. **Statistics**
   - Click "Stats" button
   - View personal statistics
   - Click "Leaderboard" to see rankings

5. **Logout**
   - Click "Logout" button
   - Should return to login screen

## Stress Testing

### Using Apache Bench

```bash
# Warm up
ab -n 100 -c 10 http://localhost:8000/api/status

# Real test
ab -n 1000 -c 50 http://localhost:8000/api/status
```

### Using wrk

```bash
# Install wrk
git clone https://github.com/wg/wrk.git
cd wrk
make

# Run test
./wrk -t12 -c400 -d30s http://localhost:8000/api/status
```

### Using Locust

```bash
# Install
pip install locust

# Create locustfile.py
# (example provided below)

# Run
locust -f locustfile.py --host=http://localhost:8000
```

#### locustfile.py Example
```python
from locust import HttpUser, task, between
import random

class GameUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Register and login
        response = self.client.post("/api/auth/register", json={
            "username": f"user_{random.randint(1, 10000)}",
            "email": f"user_{random.randint(1, 10000)}@example.com",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        
    @task(3)
    def play_game(self):
        # Create game
        response = self.client.post("/api/games/new", 
            json={
                "bet_amount": 50,
                "grid_size": 3,
                "mines_count": 1
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        if response.status_code == 200:
            game_id = response.json()["id"]
            
            # Click some cells
            for _ in range(3):
                self.client.post(f"/api/games/{game_id}/click",
                    json={"row": random.randint(0, 2), "col": random.randint(0, 2)},
                    headers={"Authorization": f"Bearer {self.token}"}
                )
    
    @task(1)
    def view_stats(self):
        self.client.get("/api/user/stats",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

## Load Testing Results

Expected performance (varies by hardware):

| Metric | Expected |
|--------|----------|
| Requests/sec | 100+ |
| Response time (p50) | < 50ms |
| Response time (p95) | < 200ms |
| Response time (p99) | < 500ms |
| CPU usage | < 70% |
| Memory usage | < 500MB |

## Database Testing

### Verify Data Integrity

```bash
# Connect to database
docker-compose exec db psql -U mineuser -d minedb

# Check users
SELECT * FROM users;

# Check games
SELECT * FROM games;

# Verify foreign keys
SELECT * FROM games WHERE user_id NOT IN (SELECT id FROM users);

# Check balance consistency
SELECT username, balance, total_wagered, total_won 
FROM users 
WHERE (total_won - total_wagered) > balance;
```

## Security Testing

### SQL Injection

```bash
# Try injection in login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin' OR '1'='1",
    "password": "anything"
  }'

# Should fail - ORM prevents injection
```

### Authentication Bypass

```bash
# Try without token
curl http://localhost:8000/api/user/profile

# Should fail with 401 Unauthorized

# Try invalid token
curl http://localhost:8000/api/user/profile \
  -H "Authorization: Bearer invalid_token"

# Should fail with 401 Unauthorized
```

### Rate Limiting

```bash
# Rapid requests should be handled gracefully
for i in {1..100}; do
  curl http://localhost:8000/api/status &
done
```

## Logging Validation

Check that sensitive data is not logged:

```bash
# View logs
docker-compose logs app | grep -i password
docker-compose logs app | grep -i token
docker-compose logs app | grep -i secret

# Should not contain actual passwords or tokens
```

## Checklist

- [ ] Registration works correctly
- [ ] Login with correct credentials works
- [ ] Login with wrong credentials fails
- [ ] JWT token validation works
- [ ] Game creation deducts balance
- [ ] Cell clicks update game state
- [ ] Mine hit ends game
- [ ] Prize claim works correctly
- [ ] Leaderboard shows correct rankings
- [ ] Logging doesn't expose sensitive data
- [ ] Concurrent users work independently
- [ ] Database integrity is maintained
- [ ] API responds to all documented endpoints
- [ ] Error messages are helpful but secure
- [ ] Performance meets expected thresholds
