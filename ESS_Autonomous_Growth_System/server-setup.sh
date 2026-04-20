#!/bin/bash
# ============================================
# ESS AGS - Server Setup Script
# Run this ONCE on your Ubuntu server (botd2)
# ============================================

set -e

echo "=== ESS Autonomous Growth System - Server Setup ==="
echo ""

# Step 1: Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[1/4] Installing Docker..."
    sudo apt update
    sudo apt install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to re-login for group changes."
else
    echo "[1/4] Docker already installed: $(docker --version)"
fi

# Step 2: Create app directory
echo "[2/4] Creating app directory..."
sudo mkdir -p /opt/ess-ags
sudo chown $USER:$USER /opt/ess-ags

# Step 3: Check if files exist
echo "[3/4] Checking for project files..."
if [ -f /opt/ess-ags/docker-compose.yml ]; then
    echo "Project files found."
else
    echo "WARNING: No project files found in /opt/ess-ags/"
    echo "You need to copy files from your Windows machine first:"
    echo ""
    echo "From Windows PowerShell:"
    echo "  scp -r C:\dev\ESS_Autonomous_Growth_System\* morningstar@192.168.1.25:/opt/ess-ags/"
    echo ""
    echo "Or use WinSCP / FileZilla to transfer the folder."
    echo ""
    echo "IMPORTANT: Do NOT copy these folders:"
    echo "  - oauth2-provider/"
    echo "  - wp-api-jwt-auth-develop/"
    echo "  - ESS - Autonomous Growth System.docx"
fi

# Step 4: Set up .env
echo "[4/4] Setting up environment..."
cd /opt/ess-ags
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo ""
        echo "=== .env created! You MUST edit it before running ==="
        echo "Run: nano /opt/ess-ags/.env"
        echo ""
        echo "Required fields:"
        echo "  WP_URL          = Your WordPress site URL"
        echo "  WP_USERNAME     = WordPress admin username"
        echo "  WP_PASSWORD     = WordPress application password"
        echo "  WP_JWT_SECRET   = Secret key from wp-config.php"
        echo "  OPENAI_API_KEY  = Your OpenAI key (or use ANTHROPIC)"
        echo "  ANTHROPIC_API_KEY = Your Anthropic key"
        echo "  LLM_PROVIDER    = openai or anthropic"
    else
        echo "ERROR: No .env.example found. Make sure project files are copied."
    fi
else
    echo ".env already exists."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Copy project files from Windows (if not done)"
echo "2. Edit .env: nano /opt/ess-ags/.env"
echo "3. Start: cd /opt/ess-ags && docker compose up -d --build"
echo "4. Check: docker compose ps"
echo "5. Logs:  docker compose logs -f api"
