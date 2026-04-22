from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import ClueUsage, GameLog, Level, Team, TeamProgress, User
from routes.admin import admin_bp
from routes.admin._helpers import admin_required, generate_team_code, log_game_action


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

    registration_code = generate_team_code()

    team = Team(name=team_name, member_names=member_names, registration_code=registration_code)
    db.session.add(team)
    db.session.commit()

    log_game_action(
        "TEAM_CREATED",
        team_id=team.id,
        details=f"Team '{team_name}' created with code {registration_code}.",
    )
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
    # Manual cascade to avoid IntegrityErrors from related rows.
    GameLog.query.filter_by(team_id=team.id).delete()
    ClueUsage.query.filter_by(team_id=team.id).delete()
    TeamProgress.query.filter_by(team_id=team.id).delete()

    team_member_ids = [u.id for u in team.members]
    if team_member_ids:
        GameLog.query.filter(GameLog.user_id.in_(team_member_ids)).delete(synchronize_session=False)
        User.query.filter(User.id.in_(team_member_ids)).delete(synchronize_session=False)

    db.session.delete(team)
    db.session.commit()
    log_game_action("TEAM_DELETED", details=f"Team '{team_name}' deleted.")
    flash('Team deleted successfully!', 'success')
    return redirect(url_for('admin.manage_teams'))
