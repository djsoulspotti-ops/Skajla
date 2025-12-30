#!/bin/bash

# ============================================
# SKAJLA - Script di Deploy Automatico Hetzner
# ============================================

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 SKAJLA - Deploy Automatico su Hetzner${NC}"
echo "============================================"
echo ""

# 1. Richiedi IP del server
read -p "Inserisci l'IP del server Hetzner: " SERVER_IP

if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}❌ IP del server obbligatorio${NC}"
    exit 1
fi

echo -e "${YELLOW}📡 Connessione al server $SERVER_IP...${NC}"

# 2. Test connessione SSH
if ! ssh -o ConnectTimeout=5 -i ~/.ssh/hetzner_key root@$SERVER_IP "echo 'Connessione OK'" 2>/dev/null; then
    echo -e "${RED}❌ Impossibile connettersi al server${NC}"
    echo "Verifica che:"
    echo "  - Il server sia acceso"
    echo "  - L'IP sia corretto"
    echo "  - La chiave SSH sia configurata su Hetzner"
    exit 1
fi

echo -e "${GREEN}✅ Connessione SSH stabilita${NC}"
echo ""

# 3. Installa Docker sul server
echo -e "${YELLOW}🐳 Installazione Docker sul server...${NC}"
ssh -i ~/.ssh/hetzner_key root@$SERVER_IP << 'ENDSSH'
    # Update system
    apt update && apt upgrade -y
    
    # Install Docker
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
        apt install docker-compose-plugin -y
        echo "✅ Docker installato"
    else
        echo "✅ Docker già installato"
    fi
    
    # Create app directory
    mkdir -p /opt/skajla
ENDSSH

echo -e "${GREEN}✅ Docker configurato${NC}"
echo ""

# 4. Copia file sul server
echo -e "${YELLOW}📦 Caricamento file sul server...${NC}"

# Crea archivio temporaneo escludendo file non necessari
tar -czf /tmp/skajla-deploy.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='node_modules' \
    --exclude='.env.secrets' \
    -C "/Users/danispotti/Desktop/SKAJLA 2" .

# Trasferisci archivio
scp -i ~/.ssh/hetzner_key /tmp/skajla-deploy.tar.gz root@$SERVER_IP:/opt/skajla/

# Estrai sul server
ssh -i ~/.ssh/hetzner_key root@$SERVER_IP << 'ENDSSH'
    cd /opt/skajla
    tar -xzf skajla-deploy.tar.gz
    rm skajla-deploy.tar.gz
ENDSSH

# Pulisci archivio locale
rm /tmp/skajla-deploy.tar.gz

echo -e "${GREEN}✅ File caricati${NC}"
echo ""

# 5. Configura variabili d'ambiente
echo -e "${YELLOW}🔐 Configurazione variabili d'ambiente...${NC}"

# Genera SECRET_KEY se non esiste
if [ ! -f .env ]; then
    SECRET_KEY=$(openssl rand -hex 32)
else
    SECRET_KEY=$(grep SECRET_KEY .env | cut -d '=' -f2)
fi

DB_PASSWORD=$(openssl rand -hex 16)

# Crea .env sul server
ssh -i ~/.ssh/hetzner_key root@$SERVER_IP << ENDSSH
    cd /opt/skajla
    cat > .env << EOF
DB_PASSWORD=$DB_PASSWORD
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
EOF
    echo "✅ File .env creato"
ENDSSH

echo -e "${GREEN}✅ Configurazione completata${NC}"
echo ""

# 6. Avvia applicazione
echo -e "${YELLOW}🚀 Avvio applicazione Docker...${NC}"

ssh -i ~/.ssh/hetzner_key root@$SERVER_IP << 'ENDSSH'
    cd /opt/skajla
    
    # Stop existing containers
    docker compose down 2>/dev/null || true
    
    # Start new containers
    docker compose up -d --build
    
    echo "✅ Applicazione avviata"
    
    # Wait for containers to start
    sleep 5
    
    # Show status
    docker compose ps
ENDSSH

echo ""
echo -e "${GREEN}✅ Deploy completato!${NC}"
echo ""
echo "============================================"
echo -e "${GREEN}📊 Informazioni Server${NC}"
echo "============================================"
echo "🌐 IP Server: $SERVER_IP"
echo "🔗 URL: http://$SERVER_IP:5000"
echo ""
echo "📝 Comandi utili:"
echo "  - Vedere i log:     ssh -i ~/.ssh/hetzner_key root@$SERVER_IP 'cd /opt/skajla && docker compose logs -f'"
echo "  - Riavviare app:    ssh -i ~/.ssh/hetzner_key root@$SERVER_IP 'cd /opt/skajla && docker compose restart'"
echo "  - Fermare app:      ssh -i ~/.ssh/hetzner_key root@$SERVER_IP 'cd /opt/skajla && docker compose down'"
echo ""
echo -e "${YELLOW}⚠️  Prossimi passi:${NC}"
echo "  1. Configura un dominio (opzionale)"
echo "  2. Installa Nginx + SSL (vedi DEPLOY_HETZNER.md)"
echo "  3. Configura firewall: ssh -i ~/.ssh/hetzner_key root@$SERVER_IP 'ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable'"
echo ""
