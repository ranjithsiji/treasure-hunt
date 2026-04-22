from datetime import datetime, timedelta

from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from app import db
from models import User
from routes.admin import admin_bp
from routes.admin._helpers import admin_required


@admin_bp.route('/reports/logged-in-users')
@login_required
@admin_required
def logged_in_users():
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    # Consider users online if is_online is True AND last_seen is within the last 5 minutes
    active_users = (
        User.query
        .filter(User.is_online == True, User.last_seen >= cutoff)  # noqa: E712
        .order_by(User.last_seen.desc())
        .all()
    )
    return render_template('admin/logged_in_users.html', active_users=active_users)


@admin_bp.route('/reports/force-logout/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def force_logout_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot force-logout an admin user.', 'warning')
    else:
        user.is_online = False
        user.session_token = None
        db.session.commit()
        flash(f'User "{user.username}" has been logged out.', 'success')
    return redirect(url_for('admin.logged_in_users'))
