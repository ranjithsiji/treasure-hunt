"""Make questions.level_id nullable to support the unassigned question pool."""
from app import create_app, db

app = create_app()
with app.app_context():
    try:
        # Drop the old NOT NULL + FK constraint, re-add as nullable with SET NULL
        db.session.execute(db.text(
            'ALTER TABLE questions MODIFY COLUMN level_id INT NULL'
        ))
        db.session.commit()
        print("questions.level_id is now nullable.")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
