"""
Database Migration Script
Adds support for multiple media files and HTML content in questions
"""

from app import create_app, db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting migration for question enhancements...")
            
            # Add points column to questions table
            try:
                db.session.execute(text(
                    "ALTER TABLE questions ADD COLUMN points INTEGER DEFAULT 10"
                ))
                print("✓ Added 'points' column to questions table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("✓ Column 'points' already exists")
                else:
                    raise
            
            # Add updated_at column to questions table
            try:
                db.session.execute(text(
                    "ALTER TABLE questions ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                ))
                print("✓ Added 'updated_at' column to questions table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("✓ Column 'updated_at' already exists")
                else:
                    raise
            
            # Create question_media table
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS question_media (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        question_id INTEGER NOT NULL,
                        media_type VARCHAR(20) NOT NULL,
                        media_url VARCHAR(500) NOT NULL,
                        media_caption VARCHAR(255),
                        display_order INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                    )
                """))
                print("✓ Created 'question_media' table")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ Table 'question_media' already exists")
                else:
                    raise
            
            # Migrate existing media_url to question_media table
            result = db.session.execute(text(
                "SELECT id, media_url, question_type FROM questions WHERE media_url IS NOT NULL AND media_url != ''"
            ))
            questions_with_media = result.fetchall()
            
            if questions_with_media:
                print(f"\nMigrating {len(questions_with_media)} existing media files...")
                for question_id, media_url, question_type in questions_with_media:
                    # Check if already migrated
                    check = db.session.execute(text(
                        "SELECT COUNT(*) FROM question_media WHERE question_id = :qid AND media_url = :url"
                    ), {"qid": question_id, "url": media_url})
                    
                    if check.scalar() == 0:
                        # Determine media type from question_type
                        media_type = 'image' if question_type == 'image' else 'video' if question_type == 'video' else 'image'
                        
                        db.session.execute(text(
                            "INSERT INTO question_media (question_id, media_type, media_url, display_order) "
                            "VALUES (:qid, :mtype, :url, 0)"
                        ), {"qid": question_id, "mtype": media_type, "url": media_url})
                
                print(f"✓ Migrated {len(questions_with_media)} media files to question_media table")
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            print("\nNew features available:")
            print("  - HTML formatting in question text")
            print("  - Multiple media files per question")
            print("  - Points system for questions")
            print("  - Media captions and ordering")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_database()
