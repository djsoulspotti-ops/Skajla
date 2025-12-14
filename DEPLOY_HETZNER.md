# Guida Deployment SKAJLA su Hetzner

## 1. Prerequisiti
- Account Hetzner Cloud
- Server VPS (minimo CX21: 2 vCPU, 4GB RAM)
- Dominio configurato (opzionale)

## 2. Setup Server Hetzner

### Crea il server
1. Vai su https://console.hetzner.cloud
2. Crea nuovo progetto "SKAJLA"
3. Aggiungi server:
   - Location: Falkenstein/Nuremberg (vicino all'Italia)
   - Image: Ubuntu 22.04
   - Type: CX21 o superiore
   - SSH Key: aggiungi la tua chiave pubblica

### Connettiti al server
```bash
ssh root@YOUR_SERVER_IP
```

### Installa Docker
```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y
```

## 3. Clone del Repository

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/skajla.git
cd skajla
```

## 4. Configurazione

```bash
cp .env.example .env
nano .env
```

Modifica le variabili:
- `DB_PASSWORD`: password sicura per PostgreSQL
- `SECRET_KEY`: stringa casuale lunga (usa `openssl rand -hex 32`)
- `GEMINI_API_KEY`: la tua chiave API Gemini

## 5. Avvia l'Applicazione

```bash
docker compose up -d
```

Verifica che tutto funzioni:
```bash
docker compose logs -f
```

## 6. Configura Nginx (Reverse Proxy + HTTPS)

```bash
apt install nginx certbot python3-certbot-nginx -y
```

Crea configurazione Nginx:
```bash
nano /etc/nginx/sites-available/skajla
```

```nginx
server {
    listen 80;
    server_name tuodominio.it www.tuodominio.it;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Attiva e ricarica:
```bash
ln -s /etc/nginx/sites-available/skajla /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Attiva HTTPS con Let's Encrypt
```bash
certbot --nginx -d tuodominio.it -d www.tuodominio.it
```

## 7. Comandi Utili

```bash
# Vedere i log
docker compose logs -f app

# Riavviare l'app
docker compose restart app

# Aggiornare dopo modifiche su GitHub
cd /opt/skajla
git pull
docker compose up -d --build

# Backup database
docker compose exec db pg_dump -U skajla skajla > backup.sql
```

## 8. Firewall

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

## Note
- Il server Hetzner CX21 costa circa 5-6€/mese
- Per traffico elevato, considera CX31 (8GB RAM)
- Hetzner ha datacenter a Falkenstein, molto veloci per l'Italia
