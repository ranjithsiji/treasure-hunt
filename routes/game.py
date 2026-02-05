from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Team, GameConfig, Level, Question, Clue, TeamProgress, ClueUsage
from app import db
from datetime import datetime

game_bp = Blueprint('game', __name__)

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

@game_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    if not current_user.team:
        flash('You are not assigned to any team. Please contact admin.', 'warning')
        return render_template('game/no_team.html')
    
    config = GameConfig.query.first()
    team = current_user.team
    
    if not config or not config.game_started:
        return render_template('game/waiting.html')
    
    current_level = Level.query.filter_by(level_number=team.current_level).first()
    
    if not current_level or not current_level.is_active:
        return render_template('game/level_locked.html', team=team, current_level=team.current_level)
    
    # Get current question
    current_question = Question.query.filter_by(
        level_id=current_level.id,
        question_number=team.current_question
    ).first()
    
    if not current_question:
        # Team has completed all questions in this level
        return render_template('game/level_complete.html', team=team, level=current_level)
    
    # Get progress for current question
    progress = TeamProgress.query.filter_by(
        team_id=team.id,
        question_id=current_question.id
    ).first()
    
    if not progress:
        # Create new progress entry
        progress = TeamProgress(
            team_id=team.id,
            question_id=current_question.id,
            level_number=current_level.level_number
        )
        db.session.add(progress)
        db.session.commit()
    
    # Get clues already used for this question
    used_clues = ClueUsage.query.filter_by(
        team_id=team.id,
        question_id=current_question.id
    ).all()
    
    used_clue_ids = [uc.clue_id for uc in used_clues]
    
    # Calculate clues remaining in current level
    used_in_level = db.session.query(db.func.count(ClueUsage.id)).join(Question).filter(
        ClueUsage.team_id == team.id,
        Question.level_id == current_level.id
    ).scalar()
    clues_remaining = max(0, current_level.clues_allowed - used_in_level)
    
    return render_template('game/play.html',
                         team=team,
                         level=current_level,
                         question=current_question,
                         progress=progress,
                         used_clue_ids=used_clue_ids,
                         clues_remaining=clues_remaining,
                         config=config)

@game_bp.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    if not current_user.team:
        return jsonify({'success': False, 'message': 'You are not assigned to any team.'})
    
    team = current_user.team
    question_id = int(request.form.get('question_id'))
    answer = request.form.get('answer', '').strip()
    
    question = Question.query.get_or_404(question_id)
    
    # Check if answer is correct (case-insensitive)
    if answer.lower() == question.answer.lower():
        # Update progress
        progress = TeamProgress.query.filter_by(
            team_id=team.id,
            question_id=question_id
        ).first()
        
        if progress and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            
            # Calculate time taken
            time_diff = progress.completed_at - progress.started_at
            progress.time_taken = int(time_diff.total_seconds())
            
            # Move to next question
            team.current_question += 1
            
            # Check for level completion and advancement
            questions_in_level = Question.query.filter_by(level_id=question.level_id).all()
            total_questions_in_level = len(questions_in_level)
            
            if team.current_question > total_questions_in_level:
                current_level_obj = Level.query.get(question.level_id)
                
                if not current_level_obj.is_final:
                    # Robust count of teams that have already advanced BEYOND this level
                    # Or are in this level but have finished it (to avoid race conditions)
                    advanced_teams = Team.query.filter(Team.current_level > current_level_obj.level_number).all()
                    advanced_count = len(advanced_teams)
                    
                    if advanced_count < current_level_obj.teams_passing:
                        # Team qualifies!
                        old_lvl = team.current_level
                        team.current_level = current_level_obj.level_number + 1
                        team.current_question = 1
                        db.session.commit() # Immediate commit for safety
                        
                        log_game_action(
                            "LEVEL_ADVANCE", 
                            team_id=team.id, 
                            details=f"Team qualified for Level {team.current_level} (Slot {advanced_count + 1}/{current_level_obj.teams_passing} filled)."
                        )
                    else:
                        log_game_action(
                            "LEVEL_COMPLETE_NOT_QUALIFIED", 
                            team_id=team.id, 
                            details=f"Team finished Level {current_level_obj.level_number} but failed to qualify (All {current_level_obj.teams_passing} slots filled)."
                        )
                else:
                    log_game_action(
                        "GAME_COMPLETE", 
                        team_id=team.id, 
                        details=f"Team has completed the final level!"
                    )
            
            db.session.commit()
            
            log_game_action(
                "SUBMIT_CORRECT_ANSWER", 
                team_id=team.id, 
                details=f"Question {question.question_number} in Level {question.level.level_number} answered correctly."
            )
            
            response_data = {
                'success': True,
                'message': 'Correct answer!',
                'redirect': url_for('game.dashboard')
            }
            
            # Add explanation if available
            if question.explanation:
                response_data['explanation'] = question.explanation
                response_data['has_explanation'] = True
            else:
                response_data['has_explanation'] = False
            
            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'message': 'Question already completed.'})
    else:
        log_game_action(
            "SUBMIT_INCORRECT_ANSWER", 
            team_id=team.id, 
            details=f"Incorrect answer '{answer}' for Question {question.question_number}."
        )
        return jsonify({'success': False, 'message': 'Incorrect answer. Try again!'})

@game_bp.route('/get-clue/<int:question_id>')
@login_required
def get_clue(question_id):
    if not current_user.team:
        return jsonify({'success': False, 'message': 'You are not assigned to any team.'})
    
    team = current_user.team
    question = Question.query.get_or_404(question_id)
    level = question.level
    
    # Calculate clues used in THIS level
    used_in_level = db.session.query(db.func.count(ClueUsage.id)).join(Question).filter(
        ClueUsage.team_id == team.id,
        Question.level_id == level.id
    ).scalar()
    
    clues_remaining_in_level = max(0, level.clues_allowed - used_in_level)
    
    if clues_remaining_in_level <= 0:
        return jsonify({'success': False, 'message': f'You have used all {level.clues_allowed} clues allowed for Level {level.level_number}.'})
    
    # Get clues for this question
    clues = Clue.query.filter_by(question_id=question_id).order_by(Clue.clue_order).all()
    
    # Get already used clues
    used_clues = ClueUsage.query.filter_by(
        team_id=team.id,
        question_id=question_id
    ).all()
    
    used_clue_ids = [uc.clue_id for uc in used_clues]
    
    # Find next unused clue
    next_clue = None
    for clue in clues:
        if clue.id not in used_clue_ids:
            next_clue = clue
            break
    
    if not clues:
        return jsonify({'success': False, 'message': 'There are no clues defined for this question.'})
        
    if not next_clue:
        return jsonify({'success': False, 'message': 'You have already used all available clues for this question.'})
    
    # Record clue usage
    clue_usage = ClueUsage(
        team_id=team.id,
        question_id=question_id,
        clue_id=next_clue.id
    )
    
    # Update progress
    progress = TeamProgress.query.filter_by(
        team_id=team.id,
        question_id=question_id
    ).first()
    
    if progress:
        progress.clues_used += 1
    
    db.session.add(clue_usage)
    db.session.commit()
    
    # Recalculate remaining for the response
    new_used_in_level = db.session.query(db.func.count(ClueUsage.id)).join(Question).filter(
        ClueUsage.team_id == team.id,
        Question.level_id == level.id
    ).scalar()
    new_remaining = max(0, level.clues_allowed - new_used_in_level)
    
    log_game_action(
        "USE_CLUE", 
        team_id=team.id, 
        details=f"Clue {next_clue.clue_order} used for Question {question.question_number} in Level {level.level_number}."
    )
    
    return jsonify({
        'success': True,
        'clue': next_clue.clue_text,
        'explanation': next_clue.explanation,
        'clues_remaining': new_remaining
    })

@game_bp.route('/join-team', methods=['GET', 'POST'])
@login_required
def join_team():
    if current_user.team:
        flash('You are already in a team.', 'info')
        return redirect(url_for('game.dashboard'))
    
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        
        if team_id:
            team = Team.query.get(int(team_id))
            if team:
                current_user.team_id = team.id
                db.session.commit()
                flash(f'Successfully joined team {team.name}!', 'success')
                return redirect(url_for('game.dashboard'))
    
    teams = Team.query.all()
    return render_template('game/join_team.html', teams=teams)

@game_bp.route('/scoreboard')
def scoreboard():
    teams = Team.query.all()
    
    # Calculate statistics for each team
    team_stats = []
    for team in teams:
        completed_questions = TeamProgress.query.filter_by(
            team_id=team.id,
            is_completed=True
        ).count()
        
        total_time = db.session.query(db.func.sum(TeamProgress.time_taken)).filter_by(
            team_id=team.id,
            is_completed=True
        ).scalar() or 0
        
        team_stats.append({
            'team': team,
            'completed_questions': completed_questions,
            'total_time': total_time,
            'current_level': team.current_level,
            'current_question': team.current_question,
            'clues_remaining': team.clues_remaining
        })
    
    # Sort by level (desc), then by questions completed (desc), then by time (asc)
    team_stats.sort(key=lambda x: (-x['current_level'], -x['completed_questions'], x['total_time']))
    
    return render_template('game/scoreboard.html', team_stats=team_stats)
