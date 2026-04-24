from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import ClueUsage, GameConfig, Team
from routes.admin import admin_bp
from routes.admin._helpers import admin_required, generate_team_code, log_game_action


@admin_bp.route('/system-settings')
@login_required
@admin_required
def system_settings():
    config = GameConfig.query.first()
    teams = Team.query.order_by(Team.name).all()

    # Clues used per team in one query
    clues_used_map = dict(
        db.session.query(ClueUsage.team_id, db.func.count(ClueUsage.id))
        .group_by(ClueUsage.team_id)
        .all()
    )

    return render_template(
        'admin/system_settings.html',
        config=config,
        teams=teams,
        clues_used_map=clues_used_map,
    )


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
        details=f"Login key changed from '{old_key}' to '{new_key}'.",
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
    log_game_action("REGISTRATION_TOGGLED", details=f"Registration window {status}.")

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
    team.code_used = False
    db.session.commit()

    log_game_action(
        "TEAM_CODE_REGENERATED",
        team_id=team.id,
        details=f"Registration code regenerated for team '{team.name}' from '{old_code}' to '{new_code}'.",
    )

    flash(f'New registration code for {team.name}: {new_code}', 'success')
    return redirect(url_for('admin.system_settings'))


@admin_bp.route('/update-global-clues', methods=['POST'])
@login_required
@admin_required
def update_global_clues():
    """Update the global clues_per_team in GameConfig."""
    config = GameConfig.query.first()
    if not config:
        flash('Game not initialised yet.', 'danger')
        return redirect(url_for('admin.system_settings'))

    try:
        new_value = max(0, int(request.form.get('clues_per_team', '')))
    except (TypeError, ValueError):
        flash('Invalid clue count.', 'danger')
        return redirect(url_for('admin.system_settings'))

    old_value = config.clues_per_team
    config.clues_per_team = new_value

    reset_overrides = request.form.get('reset_overrides') == 'on'
    if reset_overrides:
        Team.query.update({'clue_allowance': None})

    db.session.commit()
    log_game_action(
        'GLOBAL_CLUES_UPDATED',
        details=(
            f"Global clues_per_team changed from {old_value} to {new_value}."
            + (" All team overrides cleared." if reset_overrides else "")
        ),
    )
    flash(
        f'Global clue count updated to {new_value}.'
        + (' All per-team overrides have been cleared.' if reset_overrides else ''),
        'success',
    )
    return redirect(url_for('admin.system_settings'))


@admin_bp.route('/update-team-clues/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def update_team_clues(team_id):
    """Set or clear the per-team clue allowance override."""
    team = Team.query.get_or_404(team_id)
    raw = request.form.get('clue_allowance', '').strip()

    if raw == '':
        team.clue_allowance = None
        db.session.commit()
        log_game_action('TEAM_CLUES_RESET', team_id=team.id,
                        details=f"Clue override cleared for team '{team.name}' (using global default).")
        flash(f"Clue override cleared for {team.name} — now using global default.", 'success')
    else:
        try:
            value = max(0, int(raw))
        except (TypeError, ValueError):
            value = None
        if value is None:
            flash('Invalid clue count.', 'danger')
        else:
            team.clue_allowance = value
            db.session.commit()
            log_game_action('TEAM_CLUES_UPDATED', team_id=team.id,
                            details=f"Clue allowance for team '{team.name}' set to {value}.")
            flash(f"Clue allowance for {team.name} set to {value}.", 'success')

    return redirect(url_for('admin.system_settings'))
