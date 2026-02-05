from app import create_app, db
from sqlalchemy import text

app = create_app()

def migrate():
    with app.app_context():
        print("Starting GameLog migration...")
        
        # Check if game_logs table exists
        result = db.session.execute(text("SHOW TABLES LIKE 'game_logs'"))
        if not result.fetchone():
            print("Creating 'game_logs' table...")
            db.session.execute(text("""
                CREATE TABLE game_logs (
                    id INTEGER NOT NULL AUTO_INCREMENT, 
                    team_id INTEGER, 
                    user_id INTEGER, 
                    action VARCHAR(255) NOT NULL, 
                    details TEXT, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    PRIMARY KEY (id), 
                    FOREIGN KEY(team_id) REFERENCES teams (id), 
                    FOREIGN KEY(user_id) REFERENCES users (id)
                )
            """))
            db.session.commit()
            print("✓ 'game_logs' table created successfully")
        else:
            print("! 'game_logs' table already exists")

if __name__ == "__main__":
    migrate()
