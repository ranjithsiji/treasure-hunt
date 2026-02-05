from app import create_app, db
from models import Team, Level, Question, GameConfig

app = create_app()

def diagnose():
    with app.app_context():
        print("--- Game State Diagnosis ---")
        
        config = GameConfig.query.first()
        if not config:
            print("No GameConfig found.")
            return
            
        print(f"Game Config: num_teams={config.num_teams}, num_levels={config.num_levels}, game_started={config.game_started}")
        
        levels = Level.query.order_by(Level.level_number).all()
        for lvl in levels:
            q_count = Question.query.filter_by(level_id=lvl.id).count()
            print(f"Level {lvl.level_number} (ID: {lvl.id}): is_final={lvl.is_final}, teams_passing={lvl.teams_passing}, questions={q_count}")
            
        teams = Team.query.all()
        print(f"\n--- Teams (Total: {len(teams)}) ---")
        for team in teams:
            print(f"Team: {team.name}, Level: {team.current_level}, Question: {team.current_question}")
            
if __name__ == "__main__":
    diagnose()
