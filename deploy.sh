#!/bin/bash
# Quick deployment helper script

set -e

echo "=== Daily Messaging Balance Sheet - Deployment Helper ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

echo "1. Building Docker image..."
docker build -t messaging-balance-app:latest .

echo "2. Creating .env file (if not exists)..."
if [ ! -f .env ]; then
    cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ADMIN_PASS=admin
FLASK_ENV=production
EOF
    echo "Created .env file. Update SECRET_KEY and ADMIN_PASS for production!"
fi

echo "3. Starting containers with docker-compose..."
docker-compose up -d

echo "4. Waiting for app to start..."
sleep 3

echo "=========================================="
echo "App deployed successfully!"
echo "Access at: http://localhost:5000"
echo "Admin user: admin"
echo "Default password: check .env file"
echo "=========================================="
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f app"
echo "To restart: docker-compose restart app"
