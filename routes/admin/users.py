from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from models import GameLog, Team, User
from routes.admin import admin_bp
from routes.admin._helpers import admin_required


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
