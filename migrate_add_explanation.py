"""
Database Migration Script
Adds explanation field to questions table
"""

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding explanation field to questions table...")
            
            # Check if column exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'questions' "
                "AND COLUMN_NAME = 'explanation'"
            ))
            column_exists = result.scalar() > 0
            
            if column_exists:
                print("✓ Column 'explanation' already exists in 'questions' table")
            else:
                # Add the explanation column
                db.session.execute(text(
                    "ALTER TABLE questions ADD COLUMN explanation TEXT NULL"
                ))
                
                db.session.commit()
                print("✓ Added 'explanation' column to questions table")
            
            print("\n✅ Migration completed successfully!")
            print("\nNew feature available:")
            print("  - Add explanations to questions")
            print("  - Explanations shown after correct answers")
            print("  - HTML formatting supported")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_database()
