from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import User, Team, Level, Question, Clue, TeamProgress, ClueUsage, GameConfig, GameLog, QuestionMedia
from app import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import secrets
import string

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def log_game_action(action_type, team_id=None, details=None):
    """Helper function to log game actions"""
    log = GameLog(
        action=action_type,
        team_id=team_id,
        details=details
    )
    db.session.add(log)
    db.session.commit()

def generate_team_code():
    """Generate a random 8-character alphanumeric code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    config = GameConfig.query.first()
    levels = Level.query.order_by(Level.level_number).all()
    teams = Team.query.all()
    
    return render_template('admin/dashboard.html', 
                         config=config, 
                         levels=levels,
                         teams=teams)

@admin_bp.route('/initialize-game', methods=['GET', 'POST'])
@login_required
@admin_required
def initialize_game():
    if request.method == 'POST':
        num_teams = int(request.form.get('num_teams'))
        num_levels = int(request.form.get('num_levels'))
        questions_per_level = int(request.form.get('questions_per_level'))
        teams_passing_per_level = int(request.form.get('teams_passing_per_level'))
        clues_per_team = int(request.form.get('clues_per_team'))
        
        # Check if game config already exists
        config = GameConfig.query.first()
        if config:
            # Update existing config
            config.num_teams = num_teams
            config.num_levels = num_levels
            config.questions_per_level = questions_per_level
            config.teams_passing_per_level = teams_passing_per_level
            config.clues_per_team = clues_per_team
        else:
            # Create new config
            config = GameConfig(
                num_teams=num_teams,
                num_levels=num_levels,
                questions_per_level=questions_per_level,
                teams_passing_per_level=teams_passing_per_level,
                clues_per_team=clues_per_team
            )
            db.session.add(config)
        
        # Create levels if they don't exist
        existing_levels = Level.query.count()
        if existing_levels < num_levels:
            for i in range(existing_levels + 1, num_levels + 1):
                level = Level(
                    level_number=i,
                    name=f"Level {i}",
                    teams_passing=teams_passing_per_level,
                    is_final=(i == num_levels)
                )
                db.session.add(level)
        
        # Clear all game logs on initialization
        GameLog.query.delete()
        
        db.session.commit()
        
        log_game_action(
            "GAME_INITIALIZED",
            details=f"Game initialized with {num_levels} levels, {questions_per_level} questions per level."
        )
        
        flash('Game configuration saved successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    config = GameConfig.query.first()
    return render_template('admin/initialize_game.html', config=config)

@admin_bp.route('/start-game')
@login_required
@admin_required
def start_game():
    config = GameConfig.query.first()
    if not config:
        flash('Please initialize the game first.', 'warning')
        return redirect(url_for('admin.initialize_game'))
    
    # Check if there are enough teams
    teams_count = Team.query.count()
    if teams_count < config.num_teams:
        flash(f'Not enough teams. Need {config.num_teams}, have {teams_count}.', 'warning')
        return redirect(url_for('admin.manage_teams'))
    
    # Check if levels have questions
    levels = Level.query.all()
    for level in levels:
        if len(level.questions) == 0:
            flash(f'Level {level.level_number} has no questions. Please add questions to all levels first.', 'warning')
            return redirect(url_for('admin.manage_levels'))
    
    config.game_started = True
    for level in levels:
        level.is_active = True
        
    config.current_level = 1
    db.session.commit()
    
    log_game_action("GAME_STARTED", details="Game officially started. All levels activated simultaneously.")
    
    flash('Game has been started! All levels are now active and will auto-close when slots are full.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/stop-game')
@login_required
@admin_required
def stop_game():
    config = GameConfig.query.first()
    if config:
        config.game_started = False
        # Deactivate all levels
        levels = Level.query.all()
        for level in levels:
            level.is_active = False
        db.session.commit()
        
        log_game_action("GAME_STOPPED", details="Game stopped by admin.")
        flash('Game has been stopped.', 'info')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/start-level/<int:level_number>')
@login_required
@admin_required
def start_level(level_number):
    flash('Manual level activation is disabled. All levels start simultaneously when the game starts.', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/stop-level/<int:level_number>')
@login_required
@admin_required
def stop_level(level_number):
    level = Level.query.filter_by(level_number=level_number).first()
    if level:
        level.is_active = False
        db.session.commit()
        log_game_action("LEVEL_STOPPED_MANUAL", details=f"Level {level_number} manually deactivated by admin.")
        flash(f'Level {level_number} has been manually deactivated.', 'info')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/manage-levels')
@login_required
@admin_required
def manage_levels():
    levels = Level.query.order_by(Level.level_number).all()
    return render_template('admin/manage_levels.html', levels=levels)

@admin_bp.route('/update-level-config/<int:level_id>', methods=['POST'])
@login_required
@admin_required
def update_level_config(level_id):
    level = Level.query.get_or_404(level_id)
    
    level.name = request.form.get('level_name')
    level.teams_passing = int(request.form.get('teams_passing'))
    
    db.session.commit()
    
    log_game_action(
        "LEVEL_CONFIG_UPDATED",
        details=f"Level {level.level_number} config updated: {level.teams_passing} teams passing."
    )
    
    flash(f'Level {level.level_number} configuration updated successfully!', 'success')
    return redirect(url_for('admin.manage_levels'))

@admin_bp.route('/level/<int:level_id>/questions')
@login_required
@admin_required
def manage_questions(level_id):
    level = Level.query.get_or_404(level_id)
    questions = Question.query.filter_by(level_id=level_id).order_by(Question.question_number).all()
    return render_template('admin/manage_questions.html', level=level, questions=questions)

@admin_bp.route('/level/<int:level_id>/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question(level_id):
    level = Level.query.get_or_404(level_id)
    
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        answer = request.form.get('answer')
        points = int(request.form.get('points', 10))
        question_type = request.form.get('question_type', 'text')  # Default to 'text'
        
        # Get the next question number
        max_question = Question.query.filter_by(level_id=level_id).order_by(Question.question_number.desc()).first()
        next_number = (max_question.question_number + 1) if max_question else 1
        
        # Handle image upload
        media_url = None
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Create unique filename
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                media_url = f"uploads/{unique_filename}"
                # If image uploaded, set question_type to image or mixed
                if question_type == 'text':
                    question_type = 'image'
        
        question = Question(
            level_id=level_id,
            question_number=next_number,
            question_type=question_type,
            question_text=question_text,
            answer=answer,
            points=points,
            media_url=media_url
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Handle batch media uploads
        num_media = int(request.form.get('num_media', 0))
        if num_media > 0:
            for i in range(num_media):
                media_type = request.form.get(f'media_type_{i}')
                media_caption = request.form.get(f'media_caption_{i}', '')
                
                # Check if file was uploaded
                file_key = f'media_file_{i}'
                if file_key in request.files:
                    file = request.files[file_key]
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{filename}"
                        upload_folder = os.path.join('static', 'uploads', 'media')
                        os.makedirs(upload_folder, exist_ok=True)
                        file_path = os.path.join(upload_folder, unique_filename)
                        file.save(file_path)
                        
                        # Create QuestionMedia record
                        media = QuestionMedia(
                            question_id=question.id,
                            media_type=media_type,
                            media_url=f"uploads/media/{unique_filename}",
                            media_caption=media_caption,
                            display_order=i
                        )
                        db.session.add(media)
            
            db.session.commit()
        
        log_game_action(
            "QUESTION_ADDED",
            details=f"Question {next_number} added to Level {level.level_number}."
        )
        
        flash(f'Question {next_number} added successfully!', 'success')
        return redirect(url_for('admin.manage_questions', level_id=level_id))
    
    # For GET request, calculate next number
    max_question = Question.query.filter_by(level_id=level_id).order_by(Question.question_number.desc()).first()
    next_question_number = (max_question.question_number + 1) if max_question else 1
    
    return render_template('admin/add_edit_question.html', level=level, question=None, next_question_number=next_question_number)

@admin_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    level = question.level
    
    if request.method == 'POST':
        question.question_text = request.form.get('question_text')
        question.answer = request.form.get('answer')
        question.points = int(request.form.get('points', 10))
        
        # Handle image upload
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                question.media_url = f"uploads/{unique_filename}"
        
        # Handle image removal
        if request.form.get('remove_image') == 'true':
            question.media_url = None
        
        # Handle batch media deletion
        delete_media_ids = request.form.getlist('delete_media')
        if delete_media_ids:
            for media_id in delete_media_ids:
                media = QuestionMedia.query.get(int(media_id))
                if media and media.question_id == question.id:
                    db.session.delete(media)
        
        # Handle new batch media uploads
        num_media = int(request.form.get('num_media', 0))
        if num_media > 0:
            # Get current max display_order
            max_order = db.session.query(db.func.max(QuestionMedia.display_order)).filter_by(question_id=question.id).scalar() or 0
            
            for i in range(num_media):
                media_type = request.form.get(f'media_type_{i}')
                media_caption = request.form.get(f'media_caption_{i}', '')
                
                # Check if file was uploaded
                file_key = f'media_file_{i}'
                if file_key in request.files:
                    file = request.files[file_key]
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{filename}"
                        upload_folder = os.path.join('static', 'uploads', 'media')
                        os.makedirs(upload_folder, exist_ok=True)
                        file_path = os.path.join(upload_folder, unique_filename)
                        file.save(file_path)
                        
                        # Create QuestionMedia record
                        media = QuestionMedia(
                            question_id=question.id,
                            media_type=media_type,
                            media_url=f"uploads/media/{unique_filename}",
                            media_caption=media_caption,
                            display_order=max_order + i + 1
                        )
                        db.session.add(media)
        
        db.session.commit()
        
        log_game_action(
            "QUESTION_UPDATED",
            details=f"Question {question.question_number} in Level {level.level_number} updated."
        )
        
        flash(f'Question {question.question_number} updated successfully!', 'success')
        return redirect(url_for('admin.manage_questions', level_id=level.id))
    
    return render_template('admin/add_edit_question.html', level=level, question=question)

@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    level_id = question.level_id
    level_number = question.level.level_number
    question_number = question.question_number
    
    db.session.delete(question)
    db.session.commit()
    
    log_game_action(
        "QUESTION_DELETED",
        details=f"Question {question_number} deleted from Level {level_number}."
    )
    
    flash(f'Question {question_number} deleted successfully!', 'success')
    return redirect(url_for('admin.manage_questions', level_id=level_id))

@admin_bp.route('/question/<int:question_id>/clues', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_clues(question_id):
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        clue_text = request.form.get('clue_text')
        explanation = request.form.get('explanation')
        
        # Get the next clue order
        max_clue = Clue.query.filter_by(question_id=question_id).order_by(Clue.clue_order.desc()).first()
        next_order = (max_clue.clue_order + 1) if max_clue else 1
        
        clue = Clue(question_id=question_id, clue_text=clue_text, explanation=explanation, clue_order=next_order)
        db.session.add(clue)
        db.session.commit()
        flash('Clue added successfully!', 'success')
        return redirect(url_for('admin.manage_clues', question_id=question_id))
    
    clues = Clue.query.filter_by(question_id=question_id).order_by(Clue.clue_order).all()
    return render_template('admin/manage_clues.html', question=question, clues=clues)

@admin_bp.route('/clue/<int:clue_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_clue(clue_id):
    clue = Clue.query.get_or_404(clue_id)
    question_id = clue.question_id
    db.session.delete(clue)
    db.session.commit()
    flash('Clue deleted successfully!', 'success')
    return redirect(url_for('admin.manage_clues', question_id=question_id))

@admin_bp.route('/manage-teams')
@login_required
@admin_required
def manage_teams():
    teams = Team.query.all()
    levels = Level.query.all()
    return render_template('admin/manage_teams.html', teams=teams, levels=levels)

@admin_bp.route('/create-team', methods=['POST'])
@login_required
@admin_required
def create_team():
    team_name = request.form.get('team_name')
    member_names = request.form.get('member_names', '')
    
    if Team.query.filter_by(name=team_name).first():
        flash('Team name already exists!', 'danger')
        return redirect(url_for('admin.manage_teams'))
    
    # Generate unique registration code
    registration_code = generate_team_code()
    
    team = Team(name=team_name, member_names=member_names, registration_code=registration_code)
    db.session.add(team)
    db.session.commit()
    
    log_game_action("TEAM_CREATED", team_id=team.id, details=f"Team '{team_name}' created with code {registration_code}.")
    flash(f'Team created successfully! Registration Code: {registration_code}', 'success')
    return redirect(url_for('admin.manage_teams'))

@admin_bp.route('/update-team/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def update_team(team_id):
    team = Team.query.get_or_404(team_id)
    team.name = request.form.get('team_name')
    team.member_names = request.form.get('member_names', '')
    db.session.commit()
    flash('Team updated successfully!', 'success')
    return redirect(url_for('admin.manage_teams'))

@admin_bp.route('/delete-team/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    team_name = team.name
    # First, delete all associated records that point to this team
    # This acts as a manual cascade to ensure we don't hit IntegrityErrors
    GameLog.query.filter_by(team_id=team.id).delete()
    ClueUsage.query.filter_by(team_id=team.id).delete()
    TeamProgress.query.filter_by(team_id=team.id).delete()
    
    # We also need to handle Users that belong to this team
    # Users also have GameLogs, so we clean those up first too
    team_member_ids = [u.id for u in team.members]
    if team_member_ids:
        GameLog.query.filter(GameLog.user_id.in_(team_member_ids)).delete(synchronize_session=False)
        User.query.filter(User.id.in_(team_member_ids)).delete(synchronize_session=False)

    db.session.delete(team)
    db.session.commit()
    log_game_action("TEAM_DELETED", details=f"Team '{team_name}' deleted.")
    flash('Team deleted successfully!', 'success')
    return redirect(url_for('admin.manage_teams'))

@admin_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    teams = Team.query.all()
    return render_template('admin/manage_users.html', users=users, teams=teams)

@admin_bp.route('/add-user', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    team_id = request.form.get('team_id')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    
    if team_id:
        user.team_id = int(team_id)
    
    db.session.add(user)
    db.session.commit()
    flash('User created successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/assign-team/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def assign_team(user_id):
    user = User.query.get_or_404(user_id)
    team_id = request.form.get('team_id')
    
    if team_id:
        user.team_id = int(team_id)
    else:
        user.team_id = None
    
    db.session.commit()
    flash('Team assignment updated!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if user.is_admin:
        flash('Cannot delete admin users!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    username = user.username
    # Manually delete associated game logs to avoid IntegrityError
    GameLog.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password:
        flash('Password cannot be empty!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset successfully for {user.username}!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/toggle-user-status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/game-logs')
@login_required
@admin_required
def game_logs():
    team_id = request.args.get('team_id', type=int)
    
    if team_id:
        logs = GameLog.query.filter_by(team_id=team_id).order_by(GameLog.timestamp.desc()).limit(100).all()
    else:
        logs = GameLog.query.order_by(GameLog.timestamp.desc()).limit(100).all()
    
    teams = Team.query.all()
    return render_template('admin/game_logs.html', logs=logs, teams=teams, selected_team_id=team_id)

@admin_bp.route('/clear-game-logs', methods=['POST'])
@login_required
@admin_required
def clear_game_logs():
    GameLog.query.delete()
    db.session.commit()
    flash('All game logs have been cleared.', 'success')
    return redirect(url_for('admin.game_logs'))

@admin_bp.route('/level/<int:level_number>/teams')
@login_required
@admin_required
def level_teams(level_number):
    level = Level.query.filter_by(level_number=level_number).first_or_404()
    
    # Get all teams currently on this level
    teams_on_level = Team.query.filter_by(current_level=level_number).all()
    
    # Get team progress for this level
    team_data = []
    for team in teams_on_level:
        # Get progress for all questions in this level
        questions = Question.query.filter_by(level_id=level.id).order_by(Question.question_number).all()
        
        progress_data = []
        for question in questions:
            progress = TeamProgress.query.filter_by(
                team_id=team.id,
                question_id=question.id
            ).first()
            
            progress_data.append({
                'question': question,
                'progress': progress
            })
        
        team_data.append({
            'team': team,
            'progress': progress_data
        })
    
    return render_template('admin/level_teams.html', 
                         level=level, 
                         team_data=team_data)

@admin_bp.route('/team/<int:team_id>/manual-assign', methods=['POST'])
@login_required
@admin_required
def manual_assign_level(team_id):
    team = Team.query.get_or_404(team_id)
    new_level = int(request.form.get('level_number'))
    new_question = int(request.form.get('question_number', 1))
    
    old_level = team.current_level
    team.current_level = new_level
    team.current_question = new_question
    
    db.session.commit()
    
    log_game_action(
        "MANUAL_LEVEL_ASSIGN",
        team_id=team.id,
        details=f"Admin manually moved team from Level {old_level} to Level {new_level}, Q{new_question}."
    )
    
    flash(f"Team {team.name} manually moved to Level {new_level}.", "success")
    return redirect(request.referrer or url_for('admin.manage_teams'))

# System Settings Routes
@admin_bp.route('/system-settings')
@login_required
@admin_required
def system_settings():
    config = GameConfig.query.first()
    teams = Team.query.all()
    return render_template('admin/system_settings.html', config=config, teams=teams)

@admin_bp.route('/update-login-key', methods=['POST'])
@login_required
@admin_required
def update_login_key():
    config = GameConfig.query.first()
    if not config:
        flash('Game configuration not found. Please initialize the game first.', 'danger')
        return redirect(url_for('admin.initialize_game'))
    
    new_key = request.form.get('login_key')
    if not new_key:
        flash('Login key cannot be empty!', 'danger')
        return redirect(url_for('admin.system_settings'))
    
    old_key = config.login_key
    config.login_key = new_key
    db.session.commit()
    
    log_game_action(
        "LOGIN_KEY_UPDATED",
        details=f"Login key changed from '{old_key}' to '{new_key}'."
    )
    
    flash(f'Login key updated successfully to: {new_key}', 'success')
    return redirect(url_for('admin.system_settings'))

@admin_bp.route('/toggle-registration', methods=['POST'])
@login_required
@admin_required
def toggle_registration():
    config = GameConfig.query.first()
    if not config:
        flash('Game configuration not found. Please initialize the game first.', 'danger')
        return redirect(url_for('admin.initialize_game'))
    
    config.registration_enabled = not config.registration_enabled
    db.session.commit()
    
    status = 'opened' if config.registration_enabled else 'closed'
    log_game_action(
        "REGISTRATION_TOGGLED",
        details=f"Registration window {status}."
    )
    
    flash(f'Registration window has been {status}!', 'success')
    return redirect(url_for('admin.system_settings'))

@admin_bp.route('/regenerate-team-code/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def regenerate_team_code(team_id):
    team = Team.query.get_or_404(team_id)
    
    old_code = team.registration_code
    new_code = generate_team_code()
    
    team.registration_code = new_code
    team.code_used = False  # Reset usage status
    db.session.commit()
    
    log_game_action(
        "TEAM_CODE_REGENERATED",
        team_id=team.id,
        details=f"Registration code regenerated for team '{team.name}' from '{old_code}' to '{new_code}'."
    )
    
    flash(f'New registration code for {team.name}: {new_code}', 'success')
    return redirect(url_for('admin.system_settings'))
