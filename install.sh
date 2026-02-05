#!/bin/bash

# Treasure Hunt Application - Installation Script for Debian 13
# This script sets up the application with all dependencies

set -e  # Exit on error

echo "=========================================="
echo "Treasure Hunt - Installation Script"
echo "For Debian 13 with Nginx + Gunicorn"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script should be run as root or with sudo"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
APP_DIR=$(pwd)

echo "📋 Installation Configuration:"
echo "  User: $ACTUAL_USER"
echo "  App Directory: $APP_DIR"
echo ""

# Update system
echo "📦 Updating system packages..."
apt update
apt upgrade -y

# Install required system packages
echo "📦 Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    mysql-server \
    libmysqlclient-dev \
    pkg-config \
    git

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    sudo -u $ACTUAL_USER python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
sudo -u $ACTUAL_USER bash << 'EOF'
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
EOF

# Create systemd service file
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/treasure-hunt.service << EOF
[Unit]
Description=Treasure Hunt Gunicorn Service
After=network.target

[Service]
User=$ACTUAL_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 4 --bind unix:treasure-hunt.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOF

# Create wsgi.py if it doesn't exist
if [ ! -f "$APP_DIR/wsgi.py" ]; then
    echo "📝 Creating wsgi.py..."
    cat > "$APP_DIR/wsgi.py" << 'EOF'
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
EOF
    chown $ACTUAL_USER:$ACTUAL_USER "$APP_DIR/wsgi.py"
fi

# Create Nginx configuration
echo "🌐 Creating Nginx configuration..."
cat > /etc/nginx/sites-available/treasure-hunt << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain

    client_max_body_size 16M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/treasure-hunt/treasure-hunt.sock;
    }

    location /static {
        alias /path/to/treasure-hunt/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Replace placeholder path with actual path
sed -i "s|/path/to/treasure-hunt|$APP_DIR|g" /etc/nginx/sites-available/treasure-hunt

# Enable Nginx site
if [ ! -L /etc/nginx/sites-enabled/treasure-hunt ]; then
    ln -s /etc/nginx/sites-available/treasure-hunt /etc/nginx/sites-enabled/
fi

# Remove default Nginx site if it exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

# Set proper permissions
echo "🔒 Setting file permissions..."
chown -R $ACTUAL_USER:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod -R 775 "$APP_DIR/static"

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable and start services
echo "🚀 Enabling services..."
systemctl enable treasure-hunt
systemctl enable nginx

echo ""
echo "=========================================="
echo "✅ Installation completed!"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Configure your .env file:"
echo "   nano $APP_DIR/.env"
echo ""
echo "2. Run database migration:"
echo "   cd $APP_DIR"
echo "   sudo -u $ACTUAL_USER ./migrate_database.sh"
echo ""
echo "3. Run registration security migration:"
echo "   cd $APP_DIR"
echo "   sudo -u $ACTUAL_USER bash -c 'source venv/bin/activate && python migrate_registration_security.py upgrade'"
echo ""
echo "4. Start the application:"
echo "   systemctl start treasure-hunt"
echo "   systemctl restart nginx"
echo ""
echo "5. Check service status:"
echo "   systemctl status treasure-hunt"
echo "   systemctl status nginx"
echo ""
echo "6. View logs:"
echo "   journalctl -u treasure-hunt -f"
echo ""
echo "7. Update Nginx config with your domain:"
echo "   nano /etc/nginx/sites-available/treasure-hunt"
echo "   (Replace 'server_name _;' with your domain)"
echo "   systemctl restart nginx"
echo ""
