#!/bin/bash

# SKAJLA - Local Deployment Helper
# Usage: ./local_deploy.sh <SERVER_IP>

SERVER_IP=$1

if [ -z "$SERVER_IP" ]; then
    echo "⚠️ Nessun IP specificato."
    read -p "Inserisci l'indirizzo IP del server Hetzner: " SERVER_IP
    if [ -z "$SERVER_IP" ]; then
        echo "❌ IP obbligatorio. Riprova."
        exit 1
    fi
fi

echo "🚀 Starting Deployment to $SERVER_IP..."

# Define SSH Key to use
SSH_KEY=""
if [ -f "$HOME/.ssh/hetzner_key" ]; then
    echo "🔑 Found specific key: ~/.ssh/hetzner_key"
    SSH_KEY="-i $HOME/.ssh/hetzner_key"
fi

# 1. Create Directory
echo "📂 Ensuring remote directory exists..."
ssh $SSH_KEY -o StrictHostKeyChecking=no root@$SERVER_IP "mkdir -p /var/www/skajla"

# 2. Upload Code (Rsync)
echo "📦 Uploading code..."
# Exclude heavy/unnecessary local folders
rsync -avz --progress -e "ssh $SSH_KEY -o StrictHostKeyChecking=no" \
    --exclude 'venv' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '.DS_Store' \
    --exclude 'node_modules' \
    ./ root@$SERVER_IP:/var/www/skajla/

echo "✅ Upload complete."

# 3. Execute Setup Script Remotely
echo "🔧 Running setup script on server (Interactive)..."
# -t forces pseudo-tty allocation for interactive prompts
ssh $SSH_KEY -o StrictHostKeyChecking=no -t root@$SERVER_IP "cd /var/www/skajla && chmod +x setup_hetzner_server.sh && ./setup_hetzner_server.sh"

echo "🎉 Deployment Process Finished!"
