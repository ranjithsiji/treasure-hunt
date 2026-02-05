"""
Database Migration Script
Adds member_names field to teams table
"""

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding member_names field to teams table...")
            
            # Check if column exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'teams' "
                "AND COLUMN_NAME = 'member_names'"
            ))
            column_exists = result.scalar() > 0
            
            if column_exists:
                print("✓ Column 'member_names' already exists in 'teams' table")
            else:
                # Add the member_names column
                db.session.execute(text(
                    "ALTER TABLE teams ADD COLUMN member_names TEXT NULL"
                ))
                
                db.session.commit()
                print("✓ Added 'member_names' column to teams table")
            
            print("\n✅ Migration completed successfully!")
            print("\nNew feature available:")
            print("  - Add team member names in admin panel")
            print("  - Member names will be displayed to users")
            print("  - Separate from user accounts")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_database()
