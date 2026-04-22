from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Create upload folder if it doesn't exist
    os.makedirs(os.path.join(app.root_path, 'static/uploads'), exist_ok=True)

    # Context processor — cached in Flask's g so DB is hit at most once per request
    @app.context_processor
    def inject_globals():
        from models import GameConfig, MenuItem, SiteContent
        if 'game_config' not in g:
            g.game_config  = GameConfig.query.first()
            g.menu_items   = MenuItem.query.filter_by(is_active=True).order_by(MenuItem.position).all()
            g.site_content = SiteContent.query.first()
        return dict(
            game_config  = g.game_config,
            menu_items   = g.menu_items,
            site_content = g.site_content,
        )

    @app.before_request
    def update_last_seen():
        from flask_login import current_user
        from datetime import datetime, timedelta
        if current_user.is_authenticated:
            now = datetime.utcnow()
            # Only update if last_seen is missing or older than 1 minute to save DB writes
            if not current_user.last_seen or (now - current_user.last_seen).total_seconds() > 60:
                current_user.last_seen = now
                current_user.is_online = True
                db.session.commit()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.game import game_bp
    from routes.public import public_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(public_bp)

    return app

if __name__ == '__main__':
    # DB setup is handled by init_db.py — do not call create_all() here
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

