#!/bin/bash

# ==============================================================================
# SKAJLA - Script di Configurazione Server Hetzner (Ubuntu 22.04+)
# ==============================================================================

# Assicurati di eseguire questo script come root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Per favore, esegui come root"
  exit
fi

# Safety Check: Ensure running on Linux (Debian/Ubuntu)
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "⛔ STOP! Stai cercando di eseguire questo script sul tuo Mac."
  echo "👉 Questo script deve essere eseguito SOLO sul server remoto Linux."
  echo "ℹ️ Usa invece ./local_deploy.sh per caricare i file sul server."
  exit 1
fi

if ! command -v apt &> /dev/null; then
    echo "❌ Errore: Questo script richiede 'apt' (Ubuntu/Debian)."
    exit 1
fi

echo "🛠️ Inizio configurazione server SKAJLA..."

# 1. Aggiornamento Sistema
apt update && apt upgrade -y

# 2. Installazione Dipendenze di Sistema
apt install -y python3-pip python3-venv nginx git redis-server ufw

# 3. Configurazione Firewall (UFW)
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# 4. Creazione Directory e Permessi
mkdir -p /var/www/skajla
chown -R $USER:$USER /var/www/skajla

# 5. Setup Python Virtual Environment
cd /var/www/skajla
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt non trovato. Ricordati di fare il deployment prima!"
fi

# 6. Configurazione Variabili di Ambiente (.env)
if [ ! -f ".env" ]; then
    echo "📝 Creazione file .env. Inserisci i dati necessari:"
    read -p "DATABASE_URL (Neon): " db_url
    read -p "SECRET_KEY (lascia vuoto per generare): " s_key
    if [ -z "$s_key" ]; then s_key=$(python3 -c 'import secrets; print(secrets.token_hex(32))'); fi
    
    cat <<EOF > .env
ENVIRONMENT=production
DATABASE_URL=$db_url
SECRET_KEY=$s_key
REDIS_URL=redis://localhost:6379/0
PORT=5000
ALLOWED_ORIGINS=*
EOF
    echo "✅ File .env creato."
fi

# 7. Configurazione Systemd (Servizio SKAJLA)
cat <<EOF > /etc/systemd/system/skajla.service
[Unit]
Description=SKAJLA Web App
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/skajla
Environment="PATH=/var/www/skajla/venv/bin"
EnvironmentFile=/var/www/skajla/.env
ExecStart=/var/www/skajla/venv/bin/gunicorn \
    --worker-class eventlet \
    --workers 1 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    main:app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable skajla
systemctl start skajla

# 8. Configurazione Nginx
cat <<EOF > /etc/nginx/sites-available/skajla
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Supporto per WebSockets (Socket.IO)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
    }

    location /static {
        alias /var/www/skajla/static;
        expires 30d;
    }
}
EOF

ln -sf /etc/nginx/sites-available/skajla /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "✨ Configurazione completata!"
echo "📡 L'app dovrebbe essere ora raggiungibile via IP."
echo "💡 Ricordati di configurare Certbot per l'HTTPS se hai un dominio."
