from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    team = db.relationship('Team', back_populates='members')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    registration_code = db.Column(db.String(20), unique=True, nullable=True)  # Unique code for registration
    code_used = db.Column(db.Boolean, default=False)  # Track if code has been used
    current_level = db.Column(db.Integer, default=1)
    current_question = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    total_time = db.Column(db.Integer, default=0)  # in seconds
    member_names = db.Column(db.Text, nullable=True)  # Comma-separated list of team member names
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    members = db.relationship('User', back_populates='team')
    progress = db.relationship('TeamProgress', back_populates='team', cascade='all, delete-orphan')

    @property
    def clues_remaining(self):
        """Calculates clues remaining for the total game statically from config"""
        from models import GameConfig, ClueUsage
        config = GameConfig.query.first()
        if not config:
            return 0
            
        total_used = ClueUsage.query.filter_by(team_id=self.id).count()
        return max(0, config.clues_per_team - total_used)

class GameConfig(db.Model):
    __tablename__ = 'game_config'
    
    id = db.Column(db.Integer, primary_key=True)
    num_teams = db.Column(db.Integer, nullable=False)
    num_levels = db.Column(db.Integer, nullable=False)
    questions_per_level = db.Column(db.Integer, nullable=False)
    teams_passing_per_level = db.Column(db.Integer, nullable=False)
    clues_per_team = db.Column(db.Integer, nullable=False)
    current_level = db.Column(db.Integer, default=0)
    game_started = db.Column(db.Boolean, default=False)
    registration_enabled = db.Column(db.Boolean, default=True)  # Toggle registration window
    login_key = db.Column(db.String(50), nullable=True)  # Shared key for login (bot prevention)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Level(db.Model):
    __tablename__ = 'levels'
    
    id = db.Column(db.Integer, primary_key=True)
    level_number = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    teams_passing = db.Column(db.Integer, default=0)  # Number of teams that can pass to next level
    is_final = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', back_populates='level', cascade='all, delete-orphan')


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # text, image, video, mixed
    question_text = db.Column(db.Text, nullable=False)  # Now supports HTML content
    media_url = db.Column(db.String(255), nullable=True)  # Kept for backward compatibility
    answer = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, nullable=True)  # Explanation shown after correct answer (HTML supported)
    points = db.Column(db.Integer, default=10)  # Points for correct answer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    level = db.relationship('Level', back_populates='questions')
    clues = db.relationship('Clue', back_populates='question', cascade='all, delete-orphan')
    media_files = db.relationship('QuestionMedia', back_populates='question', cascade='all, delete-orphan')
    team_progress = db.relationship('TeamProgress', back_populates='question', cascade='all, delete-orphan')
    clue_usages = db.relationship('ClueUsage', back_populates='question', cascade='all, delete-orphan')


class QuestionMedia(db.Model):
    __tablename__ = 'question_media'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # image, video, audio, document
    media_url = db.Column(db.String(500), nullable=False)
    media_caption = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    question = db.relationship('Question', back_populates='media_files')


class Clue(db.Model):
    __tablename__ = 'clues'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    clue_text = db.Column(db.Text, nullable=False)
    clue_order = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text, nullable=True)  # Optional explanation for the clue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    question = db.relationship('Question', back_populates='clues')
    clue_usages = db.relationship('ClueUsage', back_populates='clue', cascade='all, delete-orphan')

class TeamProgress(db.Model):
    __tablename__ = 'team_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    level_number = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_taken = db.Column(db.Integer, default=0)  # in seconds
    clues_used = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    
    team = db.relationship('Team', back_populates='progress')
    question = db.relationship('Question', back_populates='team_progress')

class ClueUsage(db.Model):
    __tablename__ = 'clue_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    clue_id = db.Column(db.Integer, db.ForeignKey('clues.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    team = db.relationship('Team')
    question = db.relationship('Question', back_populates='clue_usages')
    clue = db.relationship('Clue', back_populates='clue_usages')

class GameLog(db.Model):
    __tablename__ = 'game_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    team = db.relationship('Team')
    user = db.relationship('User')
