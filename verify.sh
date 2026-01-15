#!/bin/bash
# Verification script - checks all files are in place

set -e

echo "================================"
echo "Project Verification"
echo "================================"
echo ""

# Count files
TOTAL_FILES=$(find . -type f ! -path '*/\.*' | wc -l)
echo "Total Files: $TOTAL_FILES"

# Check critical files
CRITICAL_FILES=(
    "main.py"
    "requirements.txt"
    "Dockerfile"
    "docker-compose.yml"
    "app/models/__init__.py"
    "app/routes/auth.py"
    "app/routes/games.py"
    "app/routes/users.py"
    "app/utils/auth.py"
    "app/utils/game_engine.py"
    "app/utils/logger.py"
    "app/database.py"
    "static/app.js"
    "static/style.css"
    "templates/index.html"
    "kubernetes/app-deployment.yaml"
    "kubernetes/postgres-deployment.yaml"
    "kubernetes/deploy.sh"
    "README.md"
    "QUICKSTART.md"
    "DEPLOYMENT.md"
    "TESTING.md"
    "ARCHITECTURE.md"
)

echo ""
echo "Checking Critical Files:"
MISSING=0
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ MISSING: $file"
        MISSING=$((MISSING + 1))
    fi
done

echo ""
if [ $MISSING -eq 0 ]; then
    echo "✅ All critical files present!"
else
    echo "❌ Missing $MISSING critical files"
    exit 1
fi

# Check file permissions
echo ""
echo "Checking Permissions:"
for script in init.sh run.sh kubernetes/deploy.sh kubernetes/undeploy.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo "✓ $script is executable"
        else
            echo "⚠ $script is NOT executable (run: chmod +x $script)"
        fi
    fi
done

# Count by type
echo ""
echo "File Statistics:"
echo "Python files: $(find . -name "*.py" -type f | wc -l)"
echo "JavaScript files: $(find . -name "*.js" -type f | wc -l)"
echo "YAML files: $(find . -name "*.yaml" -o -name "*.yml" | wc -l)"
echo "Documentation: $(find . -name "*.md" -type f | wc -l)"
echo "Configuration: $(find . -name "Makefile" -o -name "Dockerfile" -o -name ".env*" -o -name "nginx.conf" | wc -l)"

# Check directory structure
echo ""
echo "Directory Structure:"
[ -d "app" ] && echo "✓ app/" || echo "✗ app/ MISSING"
[ -d "app/models" ] && echo "✓ app/models/" || echo "✗ app/models/ MISSING"
[ -d "app/routes" ] && echo "✓ app/routes/" || echo "✗ app/routes/ MISSING"
[ -d "app/utils" ] && echo "✓ app/utils/" || echo "✗ app/utils/ MISSING"
[ -d "app/schemas" ] && echo "✓ app/schemas/" || echo "✗ app/schemas/ MISSING"
[ -d "static" ] && echo "✓ static/" || echo "✗ static/ MISSING"
[ -d "templates" ] && echo "✓ templates/" || echo "✗ templates/ MISSING"
[ -d "kubernetes" ] && echo "✓ kubernetes/" || echo "✗ kubernetes/ MISSING"
[ -d "migrations" ] && echo "✓ migrations/" || echo "✗ migrations/ MISSING"

echo ""
echo "================================"
echo "✅ Verification Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Run: ./init.sh"
echo "2. Run: docker-compose up -d"
echo "3. Visit: http://localhost:8000"
echo ""
