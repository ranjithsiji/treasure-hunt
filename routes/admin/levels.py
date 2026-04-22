from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import GameConfig, Level
from routes.admin import admin_bp
from routes.admin._helpers import admin_required, _safe_int, log_game_action


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
    config = GameConfig.query.first()

    if config and config.game_started:
        flash(
            f'⚠️ Warning: Game is live. Changes to Level {level.level_number} take effect immediately.',
            'warning',
        )

    level_name = request.form.get('level_name', '').strip() or level.name

    new_passing = _safe_int(request.form.get('teams_passing'), default=level.teams_passing, minimum=0)
    if not level.is_final and new_passing < 1:
        flash('Non-final levels must allow at least 1 team to pass. Value unchanged.', 'danger')
        return redirect(url_for('admin.manage_levels'))

    level.name = level_name
    level.teams_passing = new_passing
    db.session.commit()

    log_game_action(
        'LEVEL_CONFIG_UPDATED',
        details=(
            f'Level {level.level_number} updated: name="{level.name}", '
            f'teams_passing={level.teams_passing}'
            + (' [LIVE GAME]' if config and config.game_started else '')
        ),
    )
    flash(f'Level {level.level_number} configuration updated successfully!', 'success')
    return redirect(url_for('admin.manage_levels'))
