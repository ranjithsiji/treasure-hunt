"""Shared decorators and utilities for the admin blueprint."""
import os
import secrets
import string
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from app import db
from models import GameLog


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def log_game_action(action_type, team_id=None, details=None):
    """Helper function to log game actions."""
    log = GameLog(action=action_type, team_id=team_id, details=details)
    db.session.add(log)
    db.session.commit()


def generate_team_code():
    """Generate a random 8-character alphanumeric code."""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def _safe_int(value, default: int = 0, minimum: int = 0) -> int:
    """Parse an integer from a form value safely, clamped to a minimum."""
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return default


def _unique_filename(original_filename):
    """Generate a collision-safe filename using a random hex prefix."""
    ext = os.path.splitext(secure_filename(original_filename))[1]
    return f"{secrets.token_hex(12)}{ext}"
