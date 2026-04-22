from flask import render_template
from flask_login import login_required

from app import db
from models import GameConfig, Level, Team, ClueUsage
from routes.admin import admin_bp
from routes.admin._helpers import admin_required


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    config = GameConfig.query.first()
    levels = Level.query.order_by(Level.level_number).all()
    teams = Team.query.all()

    # Pre-aggregate clue usage in one bulk query so the template
    # never calls team.clues_remaining (2 queries × N teams) in a loop.
    clues_used_map = dict(
        db.session.query(ClueUsage.team_id, db.func.count(ClueUsage.id))
        .group_by(ClueUsage.team_id)
        .all()
    )
    clues_per_team = config.clues_per_team if config else 0
    team_clues = {
        team.id: max(0, clues_per_team - clues_used_map.get(team.id, 0))
        for team in teams
    }

    return render_template(
        'admin/dashboard.html',
        config=config,
        levels=levels,
        teams=teams,
        team_clues=team_clues,
    )
