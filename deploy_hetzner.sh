#!/bin/bash

# ==============================================================================
# SKAJLA - Script di Deployment per Hetzner
# ==============================================================================

# Configurazione del Server
SERVER_IP="37.27.252.179"
SERVER_USER="root" # Cambia in adminuser se preferisci
SSH_KEY="~/.ssh/hetzner_key"
REMOTE_PATH="/var/www/skajla"

echo "🚀 Avvio deployment di SKAJLA su Hetzner ($SERVER_IP)..."

# 1. Pulizia locale post-build
echo "🧹 Pulizia file temporanei..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# 2. Sincronizzazione file con rsync
# Escludiamo file di ambiente locali, venv e file di configurazione git
echo "📦 Sincronizzazione file in corso..."
rsync -avz -e "ssh -i $SSH_KEY" \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '.env.secrets' \
    --exclude 'skaila.db' \
    --exclude 'instance/' \
    --exclude 'logs/' \
    ./ $SERVER_USER@$SERVER_IP:$REMOTE_PATH

# 3. Riavvio del servizio sul server
echo "🔄 Riavvio del servizio SKAJLA sul server..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "systemctl restart skajla && systemctl status skajla --no-pager"

echo "✅ Deployment completato con successo!"
echo "🌐 App disponibile su: http://$SERVER_IP"
