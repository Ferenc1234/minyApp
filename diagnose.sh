#!/bin/bash
# Quick diagnostic script to check application status

echo "========================================"
echo "Application Diagnostics"
echo "========================================"
echo ""

# Check Docker
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker installed: $(docker --version)"
else
    echo "✗ Docker not found"
    exit 1
fi

echo ""
echo "2. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    echo "✓ Docker Compose installed: $(docker compose version)"
else
    echo "✗ Docker Compose not found"
    exit 1
fi

echo ""
echo "3. Checking containers..."
docker compose ps

echo ""
echo "4. Checking container health..."
DB_STATUS=$(docker compose ps db | grep "Up" | wc -l)
APP_STATUS=$(docker compose ps app | grep "Up" | wc -l)

if [ $DB_STATUS -gt 0 ]; then
    echo "✓ Database container is running"
else
    echo "✗ Database container is not running"
fi

if [ $APP_STATUS -gt 0 ]; then
    echo "✓ Application container is running"
else
    echo "✗ Application container is not running"
fi

echo ""
echo "5. Testing API availability..."
sleep 2
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API is responding at http://localhost:8000"
    echo ""
    echo "Health check response:"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "✗ API is not responding"
    echo ""
    echo "Recent application logs:"
    docker compose logs --tail=30 app
fi

echo ""
echo "6. Checking database connection..."
if docker compose exec -T db psql -U mineuser -d minedb -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
fi

echo ""
echo "7. Checking ports..."
if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "✓ Port 8000 is listening"
elif ss -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "✓ Port 8000 is listening"
else
    echo "⚠ Port 8000 might not be listening"
fi

if netstat -tuln 2>/dev/null | grep -q ":5432 "; then
    echo "✓ Port 5432 (PostgreSQL) is listening"
elif ss -tuln 2>/dev/null | grep -q ":5432 "; then
    echo "✓ Port 5432 (PostgreSQL) is listening"
else
    echo "⚠ Port 5432 (PostgreSQL) might not be listening"
fi

echo ""
echo "8. Recent errors in logs:"
echo "--- Application Errors ---"
docker compose logs --tail=20 app | grep -i "error" | tail -5 || echo "No recent errors"

echo ""
echo "--- Database Errors ---"
docker compose logs --tail=20 db | grep -i "error" | tail -5 || echo "No recent errors"

echo ""
echo "========================================"
echo "Diagnostics Complete"
echo "========================================"
