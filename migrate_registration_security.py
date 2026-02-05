"""
Migration Script: Add Registration Security Features
- Adds registration_code and code_used to teams table
- Adds registration_enabled and login_key to game_config table
"""

from app import create_app, db
from models import Team, GameConfig
import secrets
import string

def generate_team_code():
    """Generate a random 8-character alphanumeric code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def upgrade():
    """Add new columns"""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("MIGRATION: Add Registration Security Features")
        print("=" * 80)
        
        try:
            # Add columns using raw SQL
            from sqlalchemy import text
            
            print("\nStep 1: Adding 'registration_code' column to teams table...")
            try:
                db.session.execute(text(
                    "ALTER TABLE teams ADD COLUMN registration_code VARCHAR(20) UNIQUE"
                ))
                db.session.commit()
                print("✓ Successfully added 'registration_code' column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                    print("⚠ Column 'registration_code' already exists, skipping...")
                    db.session.rollback()
                else:
                    raise
            
            print("\nStep 2: Adding 'code_used' column to teams table...")
            try:
                db.session.execute(text(
                    "ALTER TABLE teams ADD COLUMN code_used BOOLEAN DEFAULT 0"
                ))
                db.session.commit()
                print("✓ Successfully added 'code_used' column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                    print("⚠ Column 'code_used' already exists, skipping...")
                    db.session.rollback()
                else:
                    raise
            
            print("\nStep 3: Generating registration codes for existing teams...")
            teams = Team.query.all()
            for team in teams:
                if not team.registration_code:
                    team.registration_code = generate_team_code()
                    team.code_used = False
            db.session.commit()
            print(f"✓ Generated codes for {len(teams)} teams")
            
            print("\nStep 4: Adding 'registration_enabled' column to game_config table...")
            try:
                db.session.execute(text(
                    "ALTER TABLE game_config ADD COLUMN registration_enabled BOOLEAN DEFAULT 1"
                ))
                db.session.commit()
                print("✓ Successfully added 'registration_enabled' column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                    print("⚠ Column 'registration_enabled' already exists, skipping...")
                    db.session.rollback()
                else:
                    raise
            
            print("\nStep 5: Adding 'login_key' column to game_config table...")
            try:
                db.session.execute(text(
                    "ALTER TABLE game_config ADD COLUMN login_key VARCHAR(50)"
                ))
                db.session.commit()
                print("✓ Successfully added 'login_key' column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                    print("⚠ Column 'login_key' already exists, skipping...")
                    db.session.rollback()
                else:
                    raise
            
            print("\nStep 6: Setting default login key...")
            config = GameConfig.query.first()
            if config and not config.login_key:
                config.login_key = generate_team_code()  # Generate a default login key
                config.registration_enabled = True
                db.session.commit()
                print(f"✓ Set default login key: {config.login_key}")
                print("  ⚠ IMPORTANT: Change this key in the admin dashboard!")
            
            print("\n" + "=" * 80)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print("\nNext Steps:")
            print("1. Login to admin dashboard")
            print("2. Go to Settings to change the login key")
            print("3. View team registration codes in Teams section")
            print("4. Toggle registration window as needed")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()
            raise

def downgrade():
    """Remove added columns"""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("ROLLBACK: Remove Registration Security Features")
        print("=" * 80)
        
        try:
            from sqlalchemy import text
            
            print("\nRemoving columns from teams table...")
            db.session.execute(text("ALTER TABLE teams DROP COLUMN registration_code"))
            db.session.execute(text("ALTER TABLE teams DROP COLUMN code_used"))
            db.session.commit()
            print("✓ Removed columns from teams table")
            
            print("\nRemoving columns from game_config table...")
            db.session.execute(text("ALTER TABLE game_config DROP COLUMN registration_enabled"))
            db.session.execute(text("ALTER TABLE game_config DROP COLUMN login_key"))
            db.session.commit()
            print("✓ Removed columns from game_config table")
            
            print("\n" + "=" * 80)
            print("ROLLBACK COMPLETED")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n✗ Rollback failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate_registration_security.py [upgrade|downgrade]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'upgrade':
        upgrade()
    elif command == 'downgrade':
        downgrade()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python migrate_registration_security.py [upgrade|downgrade]")
        sys.exit(1)
