#!/bin/bash

echo "🏆 Treasure Hunt Setup Script"
echo "=============================="
echo ""

# Check if MariaDB is installed
if ! command -v mysql &> /dev/null; then
    echo "❌ MariaDB/MySQL is not installed."
    echo "Please install MariaDB first:"
    echo "  Ubuntu/Debian: sudo apt install mariadb-server"
    echo "  Fedora/RHEL: sudo dnf install mariadb-server"
    echo "  Arch: sudo pacman -S mariadb"
    exit 1
fi

echo "✅ MariaDB/MySQL found"
echo ""

# Prompt for database credentials
read -p "Enter database name [treasure_hunt]: " DB_NAME
DB_NAME=${DB_NAME:-treasure_hunt}

read -p "Enter database username [treasure_user]: " DB_USER
DB_USER=${DB_USER:-treasure_user}

read -sp "Enter database password: " DB_PASS
echo ""

read -p "Enter database host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

echo ""
echo "Creating database and user..."

# Create database and user
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database created successfully"
else
    echo "❌ Failed to create database. Please check your MySQL root password."
    exit 1
fi

# Update .env file
echo ""
echo "Updating .env file..."

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

cat > .env << EOF
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=$SECRET_KEY
DATABASE_URI=mysql+pymysql://$DB_USER:$DB_PASS@$DB_HOST/$DB_NAME
EOF

echo "✅ .env file updated"

# Initialize database
echo ""
echo "Initializing database tables..."
uv run python init_db.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Run the application: uv run python app.py"
    echo "2. Open browser: http://localhost:5000"
    echo "3. Login with admin credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "⚠️  Remember to change the admin password after first login!"
else
    echo "❌ Database initialization failed"
    exit 1
fi
