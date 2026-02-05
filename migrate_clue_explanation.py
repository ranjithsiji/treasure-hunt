"""
Database Migration Script
Adds explanation field to clues table
"""

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding explanation field to clues table...")
            
            # Check if column exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'clues' "
                "AND COLUMN_NAME = 'explanation'"
            ))
            column_exists = result.scalar() > 0
            
            if column_exists:
                print("✓ Column 'explanation' already exists in 'clues' table")
            else:
                # Add the explanation column
                db.session.execute(text(
                    "ALTER TABLE clues ADD COLUMN explanation TEXT NULL"
                ))
                
                db.session.commit()
                print("✓ Added 'explanation' column to clues table")
            
            print("\n✅ Migration completed successfully!")
            print("\nNew feature available:")
            print("  - Add explanations to clues")
            print("  - Explanations shown to players once clue is revealed")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()
            # raise # Don't raise so we can capture output if running in background

if __name__ == '__main__':
    migrate_database()
