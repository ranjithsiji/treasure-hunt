from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import GameConfig, GameLog, Level, Question, Team
from routes.admin import admin_bp
from routes.admin._helpers import admin_required, _safe_int, log_game_action


@admin_bp.route('/initialize-game', methods=['GET', 'POST'])
@login_required
@admin_required
def initialize_game():
    if request.method == 'POST':
        num_teams = _safe_int(request.form.get('num_teams'), minimum=1)
        num_levels = _safe_int(request.form.get('num_levels'), minimum=1)
        questions_per_level = _safe_int(request.form.get('questions_per_level'), minimum=1)
        teams_passing_default = _safe_int(request.form.get('teams_passing_per_level'), minimum=1)
        clues_per_team = _safe_int(request.form.get('clues_per_team'), minimum=0)

        if not all([num_teams, num_levels, questions_per_level, teams_passing_default]):
            flash('Invalid configuration values — all fields except clues must be ≥ 1.', 'danger')
            return redirect(url_for('admin.initialize_game'))

        config = GameConfig.query.first()
        if config:
            config.num_teams = num_teams
            config.num_levels = num_levels
            config.questions_per_level = questions_per_level
            config.teams_passing_per_level = teams_passing_default
            config.clues_per_team = clues_per_team
        else:
            config = GameConfig(
                num_teams=num_teams,
                num_levels=num_levels,
                questions_per_level=questions_per_level,
                teams_passing_per_level=teams_passing_default,
                clues_per_team=clues_per_team,
            )
            db.session.add(config)

        existing_count = Level.query.count()

        if existing_count > num_levels:
            Level.query.filter(Level.level_number > num_levels).delete()

        for i in range(existing_count + 1, num_levels + 1):
            is_final_level = (i == num_levels)
            per_level_passing = _safe_int(
                request.form.get(f'teams_passing_level_{i}'),
                default=teams_passing_default,
                minimum=0 if is_final_level else 1,
            )
            level = Level(
                level_number=i,
                name=f"Level {i}",
                teams_passing=per_level_passing,
                is_final=is_final_level,
            )
            db.session.add(level)

        for level in Level.query.filter(Level.level_number <= num_levels).all():
            level.is_final = (level.level_number == num_levels)

        log_note = ""
        if not config.game_started:
            log_count = GameLog.query.count()
            GameLog.query.delete()
            log_note = f" {log_count} pre-game log(s) cleared."

        db.session.commit()

        log_game_action(
            "GAME_INITIALIZED",
            details=(
                f"Game initialized — {num_levels} levels, "
                f"{questions_per_level} questions/level, "
                f"{num_teams} teams, {clues_per_team} clues/team.{log_note}"
            ),
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

    teams_count = Team.query.count()
    if teams_count == 0:
        flash('No teams exist yet. Please create at least one team before starting.', 'warning')
        return redirect(url_for('admin.manage_teams'))

    levels = Level.query.order_by(Level.level_number).all()
    first_level = levels[0] if levels else None
    if not first_level:
        flash('No levels configured. Please initialize the game first.', 'warning')
        return redirect(url_for('admin.initialize_game'))

    first_level_q_count = Question.query.filter_by(level_id=first_level.id).count()
    if first_level_q_count == 0:
        flash('Level 1 has no questions. Add questions to Level 1 before starting.', 'warning')
        return redirect(url_for('admin.manage_levels'))

    config.game_started = True
    config.current_level = 1
    for level in levels:
        level.is_active = True
    db.session.commit()

    log_game_action(
        'GAME_STARTED',
        details=f'Game started with {teams_count} team(s). All levels activated simultaneously.',
    )
    flash('Game has been started! All levels are now active.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/stop-game')
@login_required
@admin_required
def stop_game():
    config = GameConfig.query.first()
    if config:
        try:
            config.game_started = False
            Level.query.update({'is_active': False})
            db.session.commit()
            log_game_action('GAME_STOPPED', details='Game stopped by admin.')
            flash('Game has been stopped.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Error stopping game: {e}', 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/start-level/<int:level_number>')
@login_required
@admin_required
def start_level(level_number):
    config = GameConfig.query.first()
    if not config or not config.game_started:
        flash('Cannot activate a level while the game is not running.', 'warning')
        return redirect(url_for('admin.dashboard'))

    level = Level.query.filter_by(level_number=level_number).first_or_404()
    level.is_active = True
    db.session.commit()
    log_game_action(
        'LEVEL_REOPENED',
        details=f'Level {level_number} manually re-opened by admin.',
    )
    flash(f'Level {level_number} has been re-opened.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/stop-level/<int:level_number>')
@login_required
@admin_required
def stop_level(level_number):
    level = Level.query.filter_by(level_number=level_number).first()
    if level:
        level.is_active = False
        db.session.commit()
        log_game_action(
            "LEVEL_STOPPED_MANUAL",
            details=f"Level {level_number} manually deactivated by admin.",
        )
        flash(f'Level {level_number} has been manually deactivated.', 'info')
    return redirect(url_for('admin.dashboard'))
