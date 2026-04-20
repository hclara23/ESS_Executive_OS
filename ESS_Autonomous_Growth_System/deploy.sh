#!/bin/bash
# Deploy ESS AGS to Ubuntu server (botd2 - 192.168.1.25)
# Usage: ./deploy.sh

SERVER="morningstar@192.168.1.25"
REMOTE_DIR="/opt/ess-ags"
REMOTE_PORT=8000

echo "=== ESS AGS Deployment ==="
echo "Target: $SERVER -> $REMOTE_DIR"
echo ""

# Step 1: Create remote directory
echo "[1/5] Creating remote directory..."
ssh $SERVER "sudo mkdir -p $REMOTE_DIR && sudo chown morningstar:morningstar $REMOTE_DIR"

# Step 2: Sync files (exclude junk)
echo "[2/5] Syncing files..."
rsync -avz --exclude='.env' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='oauth2-provider' \
    --exclude='wp-api-jwt-auth-develop' \
    --exclude='ESS - Autonomous Growth System.docx' \
    --exclude='.venv' \
    ./ $SERVER:$REMOTE_DIR/

# Step 3: Set up .env on server
echo "[3/5] Setting up .env..."
ssh $SERVER "cd $REMOTE_DIR && if [ ! -f .env ]; then cp .env.example .env && echo 'CREATED: .env - EDIT IT!'; else echo '.env already exists'; fi"

# Step 4: Build and start
echo "[4/5] Building and starting containers..."
ssh $SERVER "cd $REMOTE_DIR && docker compose down && docker compose up -d --build"

# Step 5: Verify
echo "[5/5] Verifying..."
sleep 5
ssh $SERVER "cd $REMOTE_DIR && docker compose ps"

echo ""
echo "=== Done ==="
echo "API:      http://192.168.1.25:$REMOTE_PORT"
echo "Docs:     http://192.168.1.25:$REMOTE_PORT/docs"
echo "n8n:      http://192.168.1.25:5678"
echo ""
echo "Edit config: ssh $SERVER 'nano $REMOTE_DIR/.env'"
echo "View logs:   ssh $SERVER 'cd $REMOTE_DIR && docker compose logs -f'"
