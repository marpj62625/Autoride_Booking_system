#!/usr/bin/env bash
set -euo pipefail

# Autoride Booking System - Hostinger Ubuntu 24.04 LTS VPS Setup Script
# Usage on VPS (as root): bash setup_vps.sh

APP_DIR="/opt/autoride"
REPO_URL="https://github.com/marpj62625/Autoride_Booking_system.git"
CUSTOMER_DOMAIN="${CUSTOMER_DOMAIN:-autoride.arcph.net}"
ADMIN_DOMAIN="${ADMIN_DOMAIN:-app.arcph.net}"
API_DOMAIN="${API_DOMAIN:-api.arcph.net}"

echo "=== 1. Updating system & installing dependencies ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git python3-venv python3-pip nginx certbot python3-certbot-nginx ufw curl

echo "=== 2. Configuring UFW firewall ==="
ufw allow OpenSSH || true
ufw allow 'Nginx Full' || true
ufw --force enable || true

echo "=== 3. Cloning or updating repository in ${APP_DIR} ==="
if [ -d "${APP_DIR}/.git" ]; then
    git -C "${APP_DIR}" fetch origin
    git -C "${APP_DIR}" reset --hard origin/main
else
    git clone "${REPO_URL}" "${APP_DIR}"
fi

echo "=== 4. Setting up Python virtualenv & requirements ==="
if [ ! -d "${APP_DIR}/venv" ]; then
    python3 -m venv "${APP_DIR}/venv"
fi
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

if [ ! -f "${APP_DIR}/.env" ]; then
    echo "WARNING: ${APP_DIR}/.env not found! Copy .env before starting autoride-api."
fi

echo "=== 5. Creating systemd service for Gunicorn (autoride-api) ==="
cat > /etc/systemd/system/autoride-api.service <<EOF
[Unit]
Description=Autoride Flask API (Gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
EnvironmentFile=-${APP_DIR}/.env
Environment="PYTHONUNBUFFERED=1"
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 120 api.index:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

chown -R www-data:www-data "${APP_DIR}"
systemctl daemon-reload
systemctl enable autoride-api
systemctl restart autoride-api

echo "=== 6. Configuring Nginx Virtual Hosts ==="
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/autoride-api <<EOF
server {
    listen 80;
    server_name ${API_DOMAIN};

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF

cat > /etc/nginx/sites-available/autoride-admin <<EOF
server {
    listen 80;
    server_name ${ADMIN_DOMAIN};

    root ${APP_DIR}/admin_app;
    index index.html;

    client_max_body_size 25M;

    location / {
        try_files \$uri \$uri.html \$uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ {
        expires 1d;
        add_header Cache-Control "public, no-transform";
    }
}
EOF

cat > /etc/nginx/sites-available/autoride-customer <<EOF
server {
    listen 80;
    server_name ${CUSTOMER_DOMAIN};

    root ${APP_DIR}/frontend;
    index index.html;

    client_max_body_size 25M;

    location / {
        try_files \$uri \$uri.html \$uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ {
        expires 1d;
        add_header Cache-Control "public, no-transform";
    }
}
EOF

ln -sf /etc/nginx/sites-available/autoride-api /etc/nginx/sites-enabled/autoride-api
ln -sf /etc/nginx/sites-available/autoride-admin /etc/nginx/sites-enabled/autoride-admin
ln -sf /etc/nginx/sites-available/autoride-customer /etc/nginx/sites-enabled/autoride-customer

nginx -t
systemctl restart nginx

echo "=== 7. Checking Gunicorn health ==="
sleep 2
systemctl status autoride-api --no-pager || true
echo ""
echo "Setup complete! Next step: run Certbot for HTTPS SSL once all DNS A-records resolve:"
echo "  certbot --nginx -d ${API_DOMAIN} -d ${ADMIN_DOMAIN} -d ${CUSTOMER_DOMAIN}"
