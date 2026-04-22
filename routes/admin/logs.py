from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import GameLog, Level, Question, Team, TeamProgress
from routes.admin import admin_bp
from routes.admin._helpers import admin_required, log_game_action


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

    teams_on_level = Team.query.filter_by(current_level=level_number).all()

    team_data = []
    for team in teams_on_level:
        questions = Question.query.filter_by(level_id=level.id).order_by(Question.question_number).all()

        progress_data = []
        for question in questions:
            progress = TeamProgress.query.filter_by(
                team_id=team.id,
                question_id=question.id,
            ).first()

            progress_data.append({
                'question': question,
                'progress': progress,
            })

        team_data.append({
            'team': team,
            'progress': progress_data,
        })

    return render_template('admin/level_teams.html', level=level, team_data=team_data)


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
        details=f"Admin manually moved team from Level {old_level} to Level {new_level}, Q{new_question}.",
    )

    flash(f"Team {team.name} manually moved to Level {new_level}.", "success")
    return redirect(request.referrer or url_for('admin.manage_teams'))
