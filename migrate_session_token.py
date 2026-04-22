"""Add session_token column to users table."""
from app import create_app, db

app = create_app()
with app.app_context():
    try:
        db.session.execute(db.text('ALTER TABLE users ADD COLUMN session_token VARCHAR(36)'))
        db.session.commit()
        print("Added session_token column.")
    except Exception as e:
        db.session.rollback()
        if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
            print("Column already exists, skipping.")
        else:
            raise
