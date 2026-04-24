"""Add clue_allowance column to teams table (per-team clue override)."""
from app import create_app, db

app = create_app()
with app.app_context():
    try:
        db.session.execute(db.text('ALTER TABLE teams ADD COLUMN clue_allowance INT NULL'))
        db.session.commit()
        print("Added clue_allowance column to teams.")
    except Exception as e:
        db.session.rollback()
        if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
            print("Column already exists, skipping.")
        else:
            raise
