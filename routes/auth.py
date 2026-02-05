from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Team
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('game.dashboard'))
    
    if request.method == 'POST':
        # Honeypot check - if filled, it's likely a bot
        if request.form.get('email_address'):
            flash('Invalid submission detected.', 'danger')
            return render_template('login.html')
        
        login_key = request.form.get('login_key')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check login key
        from models import GameConfig
        config = GameConfig.query.first()
        if config and config.login_key:
            if login_key != config.login_key:
                flash('Invalid login key. Please contact the event organizer.', 'danger')
                return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'warning')
                return render_template('login.html')
                
            login_user(user)
            next_page = request.args.get('next')
            
            if user.is_admin:
                return redirect(next_page if next_page else url_for('admin.dashboard'))
            return redirect(next_page if next_page else url_for('game.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('game.dashboard'))
    
    # Check if registration is enabled
    from models import GameConfig
    config = GameConfig.query.first()
    if config and not config.registration_enabled:
        flash('Registration is currently closed. Please contact the event organizer.', 'warning')
        return redirect(url_for('public.home'))
    
    if request.method == 'POST':
        # Honeypot check - if filled, it's likely a bot
        if request.form.get('website'):
            flash('Invalid submission detected.', 'danger')
            return render_template('register.html')
        
        team_code = request.form.get('team_code')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate team registration code
        team = Team.query.filter_by(registration_code=team_code).first()
        if not team:
            flash('Invalid team registration code. Please check your code and try again.', 'danger')
            return render_template('register.html')
        
        if team.code_used:
            flash('This registration code has already been used.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email, team_id=team.id)
        user.set_password(password)
        
        # Mark the team code as used
        team.code_used = True
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Registration successful! You have been assigned to team: {team.name}. Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.home'))
