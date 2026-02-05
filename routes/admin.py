from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Team, GameConfig, Level, Question, Clue, TeamProgress
from app import db
from functools import wraps
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def log_game_action(action, team_id=None, details=None):
    from models import GameLog
    log = GameLog(
        team_id=team_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        details=details
    )
    db.session.add(log)
    db.session.commit()

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    game_config = GameConfig.query.first()
    teams = Team.query.all()
    levels = Level.query.order_by(Level.level_number).all()
    users = User.query.filter_by(is_admin=False).all()
    
    return render_template('admin/dashboard.html', 
                         game_config=game_config, 
                         teams=teams, 
                         levels=levels,
                         users=users)

@admin_bp.route('/initialize-game', methods=['GET', 'POST'])
@login_required
@admin_required
def initialize_game():
    if request.method == 'POST':
        # Delete existing data in correct order to avoid foreign key violations
        from models import ClueUsage, TeamProgress, Clue, QuestionMedia, Question
        ClueUsage.query.delete()
        TeamProgress.query.delete()
        Clue.query.delete()
        QuestionMedia.query.delete()
        Question.query.delete()
        Level.query.delete()
        GameConfig.query.delete()
        
        num_levels = int(request.form.get('num_levels'))
        
        config = GameConfig(
            num_teams=int(request.form.get('num_teams')),
            num_levels=num_levels,
            questions_per_level=int(request.form.get('questions_per_level')),
            teams_passing_per_level=int(request.form.get('teams_passing_per_level')),
            clues_per_team=int(request.form.get('clues_per_team'))
        )
        db.session.add(config)
        
        # Create levels
        for i in range(1, num_levels + 1):
            teams_passing_key = f'teams_passing_level_{i}'
            teams_passing = int(request.form.get(teams_passing_key, 0))
            
            clues_allowed_key = f'clues_level_{i}'
            clues_allowed = int(request.form.get(clues_allowed_key, config.clues_per_team))
            
            level = Level(
                level_number=i,
                name=f"Level {i}",
                teams_passing=teams_passing,
                clues_allowed=clues_allowed,
                is_final=(i == num_levels)
            )
            db.session.add(level)
        
        # Reset teams
        from models import Team
        teams = Team.query.all()
        for team in teams:
            team.current_level = 1
            team.current_question = 1
        
        db.session.commit()
        log_game_action("INITIALIZE_GAME", details=f"Game initialized with {num_levels} levels.")
        flash('Game data reset and initialized successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/initialize_game.html')

@admin_bp.route('/start-game')
@login_required
@admin_required
def start_game():
    config = GameConfig.query.first()
    if not config:
        flash('Please initialize the game first.', 'danger')
        return redirect(url_for('admin.initialize_game'))
    
    config.game_started = True
    config.current_level = 1
    
    # Activate first level
    first_level = Level.query.filter_by(level_number=1).first()
    if first_level:
        first_level.is_active = True
    
    # Set clues for all teams
    teams = Team.query.all()
    for team in teams:
        team.current_level = 1
        team.current_question = 1
    
    db.session.commit()
    log_game_action("START_GAME", details="Game started and Level 1 activated.")
    flash('Game started! Level 1 is now active.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/stop-game')
@login_required
@admin_required
def stop_game():
    config = GameConfig.query.first()
    if config:
        config.game_started = False
        
        # Deactivate all levels
        Level.query.update({Level.is_active: False})
        
        db.session.commit()
        log_game_action("STOP_GAME", details="Game stopped manually by admin.")
        flash('Game stopped successfully.', 'warning')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/start-level/<int:level_number>')
@login_required
@admin_required
def start_level(level_number):
    config = GameConfig.query.first()
    level = Level.query.filter_by(level_number=level_number).first()
    
    if not level:
        flash('Level not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Deactivate all levels
    Level.query.update({Level.is_active: False})
    
    # Activate requested level
    level.is_active = True
    config.current_level = level_number
    
    db.session.commit()
    flash(f'Level {level_number} started!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/stop-level/<int:level_number>')
@login_required
@admin_required
def stop_level(level_number):
    level = Level.query.filter_by(level_number=level_number).first()
    
    if not level:
        flash('Level not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    level.is_active = False
    db.session.commit()
    
    flash(f'Level {level_number} stopped!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/manage-levels')
@login_required
@admin_required
def manage_levels():
    levels = Level.query.order_by(Level.level_number).all()
    game_config = GameConfig.query.first()
    return render_template('admin/manage_levels.html', levels=levels, game_config=game_config)

@admin_bp.route('/update-level-config/<int:level_id>', methods=['POST'])
@login_required
@admin_required
def update_level_config(level_id):
    level = Level.query.get_or_404(level_id)
    
    # Update teams_passing
    teams_passing = request.form.get('teams_passing')
    if teams_passing:
        level.teams_passing = int(teams_passing)
    
    # Update clues_allowed
    clues_allowed = request.form.get('clues_allowed')
    if clues_allowed is not None:
        level.clues_allowed = int(clues_allowed)
    
    # Update level name if provided
    level_name = request.form.get('level_name')
    if level_name:
        level.name = level_name
    
    db.session.commit()
    flash(f'Level {level.level_number} configuration updated!', 'success')
    return redirect(url_for('admin.manage_levels'))

@admin_bp.route('/level/<int:level_id>/questions')
@login_required
@admin_required
def manage_questions(level_id):
    """List all questions for a level"""
    level = Level.query.get_or_404(level_id)
    questions = Question.query.filter_by(level_id=level_id).order_by(Question.question_number).all()
    game_config = GameConfig.query.first()
    return render_template('admin/manage_questions.html', level=level, questions=questions, game_config=game_config)

@admin_bp.route('/level/<int:level_id>/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question(level_id):
    """Add a new question"""
    from models import QuestionMedia
    level = Level.query.get_or_404(level_id)
    
    if request.method == 'POST':
        question_type = request.form.get('question_type')
        question_text = request.form.get('question_text')  # Now contains HTML
        answer = request.form.get('answer')
        explanation = request.form.get('explanation', '')  # Optional explanation
        question_number = int(request.form.get('question_number'))
        points = int(request.form.get('points', 10))
        
        # Create question
        question = Question(
            level_id=level_id,
            question_number=question_number,
            question_type=question_type,
            question_text=question_text,
            answer=answer,
            explanation=explanation,
            points=points
        )
        
        db.session.add(question)
        db.session.flush()  # Get question ID
        
        # Handle multiple media files
        num_media = int(request.form.get('num_media', 0))
        for i in range(num_media):
            media_file_key = f'media_file_{i}'
            media_type_key = f'media_type_{i}'
            media_caption_key = f'media_caption_{i}'
            
            if media_file_key in request.files:
                file = request.files[media_file_key]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid conflicts
                    import time
                    timestamp = str(int(time.time()))
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join('static/uploads', filename)
                    file.save(filepath)
                    
                    media_url = f'/static/uploads/{filename}'
                    media_type = request.form.get(media_type_key, 'image')
                    media_caption = request.form.get(media_caption_key, '')
                    
                    media = QuestionMedia(
                        question_id=question.id,
                        media_type=media_type,
                        media_url=media_url,
                        media_caption=media_caption,
                        display_order=i
                    )
                    db.session.add(media)
        
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.manage_questions', level_id=level_id))
    
    # Get next question number
    max_question = db.session.query(db.func.max(Question.question_number)).filter_by(level_id=level_id).scalar()
    next_question_number = (max_question or 0) + 1
    
    return render_template('admin/add_edit_question.html', level=level, question=None, next_question_number=next_question_number)

@admin_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    """Edit an existing question"""
    from models import QuestionMedia
    question = Question.query.get_or_404(question_id)
    level = question.level
    
    if request.method == 'POST':
        question.question_type = request.form.get('question_type')
        question.question_text = request.form.get('question_text')  # HTML content
        question.answer = request.form.get('answer')
        question.explanation = request.form.get('explanation', '')  # Optional explanation
        question.question_number = int(request.form.get('question_number'))
        question.points = int(request.form.get('points', 10))
        
        # Handle media files
        # First, handle deletions
        delete_media_ids = request.form.getlist('delete_media')
        for media_id in delete_media_ids:
            media = QuestionMedia.query.get(int(media_id))
            if media and media.question_id == question.id:
                # Delete file from filesystem
                if media.media_url and os.path.exists(media.media_url.lstrip('/')):
                    try:
                        os.remove(media.media_url.lstrip('/'))
                    except:
                        pass
                db.session.delete(media)
        
        # Handle new media files
        num_media = int(request.form.get('num_media', 0))
        existing_media_count = len(question.media_files)
        
        for i in range(num_media):
            media_file_key = f'media_file_{i}'
            media_type_key = f'media_type_{i}'
            media_caption_key = f'media_caption_{i}'
            
            if media_file_key in request.files:
                file = request.files[media_file_key]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    import time
                    timestamp = str(int(time.time()))
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join('static/uploads', filename)
                    file.save(filepath)
                    
                    media_url = f'/static/uploads/{filename}'
                    media_type = request.form.get(media_type_key, 'image')
                    media_caption = request.form.get(media_caption_key, '')
                    
                    media = QuestionMedia(
                        question_id=question.id,
                        media_type=media_type,
                        media_url=media_url,
                        media_caption=media_caption,
                        display_order=existing_media_count + i
                    )
                    db.session.add(media)
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin.manage_questions', level_id=question.level_id))
    
    return render_template('admin/add_edit_question.html', level=level, question=question, next_question_number=None)

@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    from models import QuestionMedia
    question = Question.query.get_or_404(question_id)
    level_id = question.level_id
    
    # Delete associated media files from filesystem
    for media in question.media_files:
        if media.media_url and os.path.exists(media.media_url.lstrip('/')):
            try:
                os.remove(media.media_url.lstrip('/'))
            except:
                pass
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.manage_questions', level_id=level_id))

@admin_bp.route('/question/<int:question_id>/clues', methods=['GET', 'POST'])

@login_required
@admin_required
def manage_clues(question_id):
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        clue_text = request.form.get('clue_text')
        clue_order = int(request.form.get('clue_order'))
        explanation = request.form.get('explanation')
        
        clue = Clue(
            question_id=question_id,
            clue_text=clue_text,
            clue_order=clue_order,
            explanation=explanation
        )
        
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
    from models import Level
    teams = Team.query.all()
    levels = Level.query.all()
    return render_template('admin/manage_teams.html', teams=teams, levels=levels)

@admin_bp.route('/create-team', methods=['POST'])
@login_required
@admin_required
def create_team():
    team_name = request.form.get('team_name')
    member_names = request.form.get('member_names')
    
    if Team.query.filter_by(name=team_name).first():
        flash('Team name already exists.', 'danger')
        return redirect(url_for('admin.manage_teams'))
    
    config = GameConfig.query.first()
    team = Team(
        name=team_name,
        member_names=member_names
    )
    
    db.session.add(team)
    db.session.commit()
    
    flash('Team created successfully!', 'success')
    return redirect(url_for('admin.manage_teams'))

@admin_bp.route('/update-team/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def update_team(team_id):
    team = Team.query.get_or_404(team_id)
    team.name = request.form.get('team_name')
    team.member_names = request.form.get('member_names')
    
    db.session.commit()
    
    flash('Team updated successfully!', 'success')
    return redirect(url_for('admin.manage_teams'))

@admin_bp.route('/delete-team/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    
    # Remove team association from users
    User.query.filter_by(team_id=team_id).update({User.team_id: None})
    
    db.session.delete(team)
    db.session.commit()
    
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
    team_id = request.form.get('team_id')
    is_admin = request.form.get('is_admin') == '1'
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    
    if team_id:
        user.team_id = int(team_id)
        
    db.session.add(user)
    db.session.commit()
    
    flash(f'User {username} created successfully!', 'success')
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
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    # Prevent deleting other admins if needed? Usually one admin can't delete another?
    # Let's just allow it for now but maybe keep it restricted to non-admins if desired.
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password for {user.username} has been reset.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/toggle-user-status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activated" if user.is_active else "deactivated"
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/game-logs')
@login_required
@admin_required
def game_logs():
    from models import GameLog, Team
    team_id = request.args.get('team_id', type=int)
    
    query = GameLog.query
    if team_id:
        query = query.filter_by(team_id=team_id)
        
    logs = query.order_by(GameLog.timestamp.desc()).all()
    teams = Team.query.all()
    
    return render_template('admin/game_logs.html', logs=logs, teams=teams, selected_team_id=team_id)

@admin_bp.route('/level/<int:level_number>/teams')
@login_required
@admin_required
def level_teams(level_number):
    from models import TeamProgress, Level
    level = Level.query.filter_by(level_number=level_number).first_or_404()
    
    # Get all teams that are currently in this level or HAVE BEEN in this level and passed
    # Actually, the user asked for "teams in this level" but also "finished the level in the order of time"
    # So we show teams whose current_level is >= level_number
    
    teams = Team.query.filter(Team.current_level >= level_number).all()
    q_count = len(level.questions)
    
    # Enrich teams with ranking data
    team_stats = []
    for team in teams:
        # Get progress for all questions of THIS level to find the "latest" completion time
        current_level_progress = TeamProgress.query.join(Question).filter(
            TeamProgress.team_id == team.id,
            Question.level_id == level.id,
            TeamProgress.is_completed == True
        ).order_by(TeamProgress.completed_at.desc()).first()
        
        last_action_time = current_level_progress.completed_at if current_level_progress else None
        
        is_actually_finished = team.current_level > level_number or (team.current_level == level_number and team.current_question > q_count)
        
        team_stats.append({
            'team': team,
            'status': "Passed" if team.current_level > level_number else "Current",
            'finished': is_actually_finished,
            'finish_time': last_action_time,
            'current_q': min(team.current_question if team.current_level == level_number else q_count, q_count),
            'sort_key': (
                1 if is_actually_finished else 0, # Finished teams on top
                team.current_question if team.current_level == level_number else q_count + 1, # Then by question number
                -(last_action_time.timestamp()) if last_action_time else -9999999999 # Then by who got there first
            )
        })
    
    # Sort teams: Finished first (by time), then by question count
    team_stats.sort(key=lambda x: x['sort_key'], reverse=True)
    
    all_levels = Level.query.order_by(Level.level_number).all()
    
    return render_template('admin/level_teams.html', 
                          level=level, 
                          team_stats=team_stats, 
                          all_levels=all_levels)

@admin_bp.route('/team/<int:team_id>/manual-assign', methods=['POST'])
@login_required
@admin_required
def manual_assign_level(team_id):
    team = Team.query.get_or_404(team_id)
    new_level = request.form.get('level_number', type=int)
    new_question = request.form.get('question_number', type=int, default=1)
    
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
