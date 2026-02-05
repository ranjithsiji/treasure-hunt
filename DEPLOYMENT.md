# Treasure Hunt - Deployment Guide for Debian 13

This guide will help you deploy the Treasure Hunt application on a Debian 13 server with Nginx and Gunicorn.

## Prerequisites

- Debian 13 server with root access
- MySQL database created
- Domain name (optional, can use IP address)

## Quick Start

### 1. Upload Application to Server

```bash
# On your local machine
cd /home/alphaf42/treasure-hunt
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
    . user@your-server:/var/www/treasure-hunt/
```

Or clone from Git:
```bash
# On server
cd /var/www
git clone <your-repo-url> treasure-hunt
cd treasure-hunt
```

### 2. Create .env File

```bash
cd /var/www/treasure-hunt
nano .env
```

Add the following content:
```env
# Flask Settings
FLASK_APP=app.py
FLASK_DEBUG=0
SECRET_KEY=your-secret-key-here-generate-a-random-string

# Database Credentials
DB_USER=treasure_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_NAME=treasure_hunt
DB_PORT=3306
```

**Generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Create MySQL Database

```bash
# Login to MySQL
sudo mysql -u root -p

# Create database and user
CREATE DATABASE treasure_hunt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'treasure_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON treasure_hunt.* TO 'treasure_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Run Installation Script

```bash
cd /var/www/treasure-hunt
chmod +x install.sh migrate_database.sh
sudo ./install.sh
```

This script will:
- Install system dependencies (Python, Nginx, MySQL client, etc.)
- Create Python virtual environment
- Install Python packages
- Create Gunicorn systemd service
- Configure Nginx
- Set proper file permissions

### 5. Run Database Migrations

```bash
# Create database tables
./migrate_database.sh

# Run registration security migration
source venv/bin/activate
python migrate_registration_security.py upgrade
deactivate
```

### 6. Start Services

```bash
# Start Gunicorn service
sudo systemctl start treasure-hunt
sudo systemctl status treasure-hunt

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl status nginx
```

### 7. Configure Domain (Optional)

Edit Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/treasure-hunt
```

Change `server_name _;` to your domain:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

Restart Nginx:
```bash
sudo systemctl restart nginx
```

### 8. Setup SSL with Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
```

## Service Management

### Start/Stop/Restart Application

```bash
# Start
sudo systemctl start treasure-hunt

# Stop
sudo systemctl stop treasure-hunt

# Restart
sudo systemctl restart treasure-hunt

# Status
sudo systemctl status treasure-hunt

# Enable auto-start on boot
sudo systemctl enable treasure-hunt
```

### View Logs

```bash
# Application logs
sudo journalctl -u treasure-hunt -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

## Updating the Application

```bash
# Stop the service
sudo systemctl stop treasure-hunt

# Pull latest changes (if using Git)
cd /var/www/treasure-hunt
git pull

# Or upload new files via rsync

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run any new migrations
python migrate_registration_security.py upgrade

# Deactivate virtual environment
deactivate

# Restart the service
sudo systemctl start treasure-hunt
```

## Troubleshooting

### Application won't start

```bash
# Check service status
sudo systemctl status treasure-hunt

# Check logs
sudo journalctl -u treasure-hunt -n 50

# Check if socket file exists
ls -la /var/www/treasure-hunt/treasure-hunt.sock

# Check permissions
ls -la /var/www/treasure-hunt/
```

### Nginx 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status treasure-hunt

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Verify socket path in Nginx config
sudo nano /etc/nginx/sites-available/treasure-hunt
```

### Database connection errors

```bash
# Verify .env file
cat /var/www/treasure-hunt/.env

# Test MySQL connection
mysql -u treasure_user -p treasure_hunt

# Check if database exists
mysql -u root -p -e "SHOW DATABASES;"
```

### Permission errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/treasure-hunt

# Fix permissions
sudo chmod -R 755 /var/www/treasure-hunt
sudo chmod -R 775 /var/www/treasure-hunt/static
```

## File Structure

```
/var/www/treasure-hunt/
├── app.py                          # Flask application factory
├── wsgi.py                         # WSGI entry point
├── config.py                       # Configuration
├── models.py                       # Database models
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
├── install.sh                     # Installation script
├── migrate_database.sh            # Database migration script
├── migrate_registration_security.py
├── routes/                        # Application routes
│   ├── admin.py
│   ├── auth.py
│   ├── game.py
│   └── public.py
├── templates/                     # HTML templates
├── static/                        # Static files (CSS, JS, images)
└── venv/                         # Virtual environment (created by install.sh)
```

## Default Credentials

After running `migrate_database.sh`:

- **Admin Username:** admin
- **Admin Password:** admin123
- **Login Key:** THARANG2026

**⚠️ IMPORTANT:** Change these immediately after first login!

## Security Checklist

- [ ] Change admin password
- [ ] Update login key in System Settings
- [ ] Generate strong SECRET_KEY in .env
- [ ] Use strong database password
- [ ] Enable firewall (ufw)
- [ ] Setup SSL certificate
- [ ] Regular backups of database
- [ ] Keep system packages updated

## Backup

### Database Backup

```bash
# Create backup
mysqldump -u treasure_user -p treasure_hunt > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
mysql -u treasure_user -p treasure_hunt < backup_20260205_235959.sql
```

### Full Application Backup

```bash
# Backup everything
tar -czf treasure-hunt-backup-$(date +%Y%m%d).tar.gz \
    /var/www/treasure-hunt \
    --exclude=venv \
    --exclude=__pycache__
```

## Performance Tuning

### Gunicorn Workers

Edit `/etc/systemd/system/treasure-hunt.service`:
```ini
# Formula: (2 x CPU cores) + 1
ExecStart=/var/www/treasure-hunt/venv/bin/gunicorn --workers 4 --bind unix:treasure-hunt.sock -m 007 wsgi:app
```

### Nginx Caching

Add to `/etc/nginx/sites-available/treasure-hunt`:
```nginx
location /static {
    alias /var/www/treasure-hunt/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u treasure-hunt -f`
2. Verify configuration files
3. Check file permissions
4. Review this deployment guide

## License

[Your License Here]
