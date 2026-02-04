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
        # Delete existing configuration
        GameConfig.query.delete()
        
        num_levels = int(request.form.get('num_levels'))
        
        config = GameConfig(
            num_teams=int(request.form.get('num_teams')),
            num_levels=num_levels,
            questions_per_level=int(request.form.get('questions_per_level')),
            teams_passing_per_level=int(request.form.get('teams_passing_per_level')),  # Keep for backward compatibility
            clues_per_team=int(request.form.get('clues_per_team'))
        )
        
        db.session.add(config)
        
        # Create levels with individual teams_passing configuration
        Level.query.delete()
        for i in range(1, num_levels + 1):
            # Get teams_passing for this specific level from form
            teams_passing_key = f'teams_passing_level_{i}'
            teams_passing = int(request.form.get(teams_passing_key, 0))
            
            level = Level(
                level_number=i,
                name=f"Level {i}",
                teams_passing=teams_passing,
                is_final=(i == num_levels)
            )
            db.session.add(level)
        
        db.session.commit()
        flash('Game initialized successfully with per-level team passing configuration!', 'success')
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
        team.clues_remaining = config.clues_per_team
        team.current_level = 1
        team.current_question = 1
    
    db.session.commit()
    flash('Game started! Level 1 is now active.', 'success')
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
        
        clue = Clue(
            question_id=question_id,
            clue_text=clue_text,
            clue_order=clue_order
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
    teams = Team.query.all()
    return render_template('admin/manage_teams.html', teams=teams)

@admin_bp.route('/create-team', methods=['POST'])
@login_required
@admin_required
def create_team():
    team_name = request.form.get('team_name')
    
    if Team.query.filter_by(name=team_name).first():
        flash('Team name already exists.', 'danger')
        return redirect(url_for('admin.manage_teams'))
    
    config = GameConfig.query.first()
    team = Team(
        name=team_name,
        clues_remaining=config.clues_per_team if config else 0
    )
    
    db.session.add(team)
    db.session.commit()
    
    flash('Team created successfully!', 'success')
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
    users = User.query.filter_by(is_admin=False).all()
    teams = Team.query.all()
    return render_template('admin/manage_users.html', users=users, teams=teams)

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
