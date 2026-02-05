#!/bin/bash

# Treasure Hunt Application - Database Migration Script
# This script creates all necessary database tables

set -e  # Exit on error

echo "=========================================="
echo "Treasure Hunt - Database Migration"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with database credentials"
    exit 1
fi

# Load environment variables
source .env

echo "📊 Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

echo "🗄️  Creating database tables..."
python3 << 'PYTHON_SCRIPT'
from app import create_app, db
from models import User, Team, Level, Question, Clue, TeamProgress, ClueUsage, GameConfig, GameLog

app = create_app()

with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("✅ All tables created successfully!")
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("\n👤 Creating default admin user...")
        admin = User(
            username='admin',
            email='admin@treasurehunt.local',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  IMPORTANT: Change this password immediately!")
    else:
        print("\n✅ Admin user already exists")
    
    # Check if game config exists
    config = GameConfig.query.first()
    if not config:
        print("\n⚙️  Creating default game configuration...")
        config = GameConfig(
            num_teams=10,
            num_levels=3,
            questions_per_level=5,
            teams_passing_per_level=5,
            clues_per_team=3,
            registration_enabled=True,
            login_key='THARANG2026'
        )
        db.session.add(config)
        db.session.commit()
        print("✅ Game configuration created!")
        print("   Default login key: THARANG2026")
        print("   ⚠️  Change this in System Settings!")
    else:
        print("\n✅ Game configuration already exists")

PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ Database migration completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Login to admin panel: http://your-domain/auth/login"
echo "2. Username: admin, Password: admin123"
echo "3. Change admin password in User Management"
echo "4. Update login key in System Settings"
echo "5. Initialize game configuration"
echo ""
