"""
Database Migration Script
Adds teams_passing column to levels table
"""

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'levels' "
                "AND COLUMN_NAME = 'teams_passing'"
            ))
            column_exists = result.scalar() > 0
            
            if column_exists:
                print("✓ Column 'teams_passing' already exists in 'levels' table")
            else:
                print("Adding 'teams_passing' column to 'levels' table...")
                
                # Add the column
                db.session.execute(text(
                    "ALTER TABLE levels ADD COLUMN teams_passing INTEGER DEFAULT 0"
                ))
                
                # Update existing levels with default value from game_config
                db.session.execute(text(
                    "UPDATE levels l "
                    "JOIN game_config gc ON 1=1 "
                    "SET l.teams_passing = gc.teams_passing_per_level "
                    "WHERE l.is_final = 0"
                ))
                
                # Set final level to 0
                db.session.execute(text(
                    "UPDATE levels SET teams_passing = 0 WHERE is_final = 1"
                ))
                
                db.session.commit()
                print("✓ Migration completed successfully!")
                print("✓ Existing levels updated with default teams_passing values")
            
        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_database()
