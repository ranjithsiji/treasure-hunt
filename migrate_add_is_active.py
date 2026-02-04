"""
Database Migration Script
Adds is_active field to users table
"""

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding is_active field to users table...")
            
            # Check if column exists
            # Using a more portable way for SQLite/MySQL
            try:
                db.session.execute(text("SELECT is_active FROM users LIMIT 1"))
                print("✓ Column 'is_active' already exists in 'users' table")
                return
            except Exception:
                # Column doesn't exist, proceed with addition
                pass
            
            # Add the is_active column with default value 1 (True)
            # SQLite doesn't support adding a column with DEFAULT in a single step always the same way,
            # but standard SQL is ALTER TABLE [table] ADD COLUMN [column] [type] DEFAULT [value]
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"
            ))
            
            db.session.commit()
            print("✓ Added 'is_active' column to users table")
            
            print("\n✅ Migration completed successfully!")
            print("\nNew feature available:")
            print("  - Enable/Disable user accounts")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_database()
