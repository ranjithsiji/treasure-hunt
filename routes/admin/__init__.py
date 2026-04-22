"""Admin blueprint package — routes are split across submodules by function."""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import submodules so their @admin_bp.route decorators register.
from routes.admin import (  # noqa: E402,F401
    dashboard,
    game_control,
    levels,
    questions,
    clues,
    teams,
    users,
    logs,
    settings,
    cms,
    reports,
)
