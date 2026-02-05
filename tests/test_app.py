import pytest
import os
import tempfile
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Create isolated test instances
test_db = SQLAlchemy()
test_login_manager = LoginManager()

@pytest.fixture(scope='function')
def app():
    """Create and configure a test app instance with isolated database."""
    # Set up a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create a minimal test app
    test_app = Flask(__name__)
    test_app.config['SECRET_KEY'] = 'test-secret-key'
    test_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize extensions with test app
    test_db.init_app(test_app)
    test_login_manager.init_app(test_app)
    test_login_manager.login_view = 'auth.login'
    
    # Import models after db is initialized
    with test_app.app_context():
        from models import User, Team, Level, Question, Clue, ClueUsage, GameConfig, TeamProgress
        
        # Create tables
        test_db.create_all()
        
        # Create an admin user
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        test_db.session.add(admin)
        test_db.session.commit()
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.game import game_bp
    from routes.public import public_bp
    
    test_app.register_blueprint(auth_bp, url_prefix='/auth')
    test_app.register_blueprint(admin_bp, url_prefix='/admin')
    test_app.register_blueprint(game_bp, url_prefix='/game')
    test_app.register_blueprint(public_bp)
    
    yield test_app
    
    # Teardown
    with test_app.app_context():
        test_db.session.remove()
        test_db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth(client):
    class Auth:
        def login(self, username='admin', password='admin123'):
            return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)
        def logout(self):
            return client.get('/auth/logout', follow_redirects=True)
    return Auth()

def test_initialization(client, auth):
    auth.login()
    # Test initialization with 2 levels, 5 questions, 2 clues per team
    response = client.post('/admin/initialize-game', data={
        'num_teams': 5,
        'num_levels': 2,
        'questions_per_level': 5,
        'teams_passing_per_level': 3,
        'clues_per_team': 2,
        'teams_passing_level_1': 3,
        'clues_level_1': 2,
        'teams_passing_level_2': 0,
        'clues_level_2': 5
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    with client.application.app_context():
        from models import Level, GameConfig
        levels = Level.query.all()
        assert len(levels) == 2
        assert levels[0].clues_allowed == 2
        assert levels[1].clues_allowed == 5
        
        config = GameConfig.query.first()
        assert config.num_levels == 2

def test_clue_logic_level_specific(client, auth):
    auth.login()
    # Initialize game
    client.post('/admin/initialize-game', data={
        'num_teams': 2,
        'num_levels': 2,
        'questions_per_level': 2,
        'teams_passing_per_level': 1,
        'clues_per_team': 1,
        'teams_passing_level_1': 1,
        'clues_level_1': 1, # Only 1 clue for level 1
        'teams_passing_level_2': 0,
        'clues_level_2': 3  # 3 clues for level 2
    }, follow_redirects=True)
    
    with client.application.app_context():
        from models import User, Team, Level, Question, Clue
        # Register a team/user
        user = User(username='player1', email='p1@ex.com')
        user.set_password('pass123')
        team = Team(name='Team 1', current_level=1, current_question=1)
        test_db.session.add(user)
        test_db.session.add(team)
        test_db.session.commit()
        user.team_id = team.id
        test_db.session.commit()
        
        # Add a question and a clue to level 1
        level1 = Level.query.filter_by(level_number=1).first()
        q1 = Question(level_id=level1.id, question_number=1, question_type='text', question_text='Q1', answer='A1')
        test_db.session.add(q1)
        test_db.session.commit()
        
        c1 = Clue(question_id=q1.id, clue_text='Clue 1', clue_order=1)
        c2 = Clue(question_id=q1.id, clue_text='Clue 2', clue_order=2)
        test_db.session.add(c1)
        test_db.session.add(c2)
        test_db.session.commit()
        
        q1_id = q1.id
        p1_id = user.id

    # Login as player
    auth.logout()
    auth.login('player1', 'pass123')
    
    # Request first clue
    res = client.get(f'/game/get-clue/{q1_id}')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['clues_remaining'] == 0 # Used 1 of 1
    
    # Request second clue (should fail due to level limit)
    res = client.get(f'/game/get-clue/{q1_id}')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is False
    assert 'all 1 clues allowed for Level 1' in data['message']

    # Advance team to level 2
    with client.application.app_context():
        from models import Team, Level, Question, Clue
        team = Team.query.filter_by(name='Team 1').first()
        team.current_level = 2
        team.current_question = 1
        
        level2 = Level.query.filter_by(level_number=2).first()
        q2 = Question(level_id=level2.id, question_number=1, question_type='text', question_text='Q2', answer='A2')
        test_db.session.add(q2)
        test_db.session.commit()
        
        clue_lev2 = Clue(question_id=q2.id, clue_text='Level 2 Clue', clue_order=1)
        test_db.session.add(clue_lev2)
        test_db.session.commit()
        q2_id = q2.id

    # Request clue in level 2 (should be allowed, quota is 3)
    res = client.get(f'/game/get-clue/{q2_id}')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['clues_remaining'] == 2 # 3 - 1 = 2

def test_admin_manual_assign(client, auth):
    auth.login()
    # Initialize game
    client.post('/admin/initialize-game', data={
        'num_teams': 2,
        'num_levels': 3,
        'questions_per_level': 2,
        'teams_passing_per_level': 1,
        'clues_per_team': 3,
        'teams_passing_level_1': 1,
        'clues_level_1': 3,
        'teams_passing_level_2': 1,
        'clues_level_2': 3,
        'teams_passing_level_3': 0,
        'clues_level_3': 3
    }, follow_redirects=True)
    
    with client.application.app_context():
        from models import Team
        team = Team(name='Test Team', current_level=1, current_question=1)
        test_db.session.add(team)
        test_db.session.commit()
        team_id = team.id
        
    # Manually move to level 2, question 2
    response = client.post(f'/admin/team/{team_id}/manual-assign', data={
        'level_number': 2,
        'question_number': 2
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    with client.application.app_context():
        from models import Team
        team = Team.query.get(team_id)
        assert team.current_level == 2
        assert team.current_question == 2
