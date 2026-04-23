"""Flask CLI commands — run with `flask user <command>`."""
import click
from flask import Blueprint
from flask.cli import with_appcontext

user_cli = Blueprint('user', __name__, cli_group='user')


@user_cli.cli.command('list')
@with_appcontext
def list_users():
    """List all users (admins shown with [ADMIN] tag)."""
    from models import User
    users = User.query.order_by(User.is_admin.desc(), User.username).all()
    if not users:
        click.echo('No users found.')
        return
    click.echo(f'\n{"ID":<5} {"Username":<20} {"Email":<30} {"Role":<8} {"Active":<8} {"Online"}')
    click.echo('-' * 80)
    for u in users:
        role  = click.style('ADMIN', fg='yellow') if u.is_admin else 'user'
        active = click.style('yes', fg='green') if u.is_active else click.style('no', fg='red')
        online = click.style('online', fg='cyan') if u.is_online else 'offline'
        click.echo(f'{u.id:<5} {u.username:<20} {u.email:<30} {role:<8} {active:<8} {online}')
    click.echo()


@user_cli.cli.command('reset-password')
@click.argument('username')
@click.password_option('--password', prompt='New password', confirmation_prompt=True)
@with_appcontext
def reset_password(username, password):
    """Reset password for USERNAME."""
    from app import db
    from models import User
    user = User.query.filter_by(username=username).first()
    if not user:
        raise click.ClickException(f'User "{username}" not found.')
    user.set_password(password)
    # Invalidate any active session so the new password takes effect immediately
    user.session_token = None
    user.is_online = False
    db.session.commit()
    click.echo(click.style(f'Password reset for "{username}".', fg='green'))


@user_cli.cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.password_option('--password', prompt='Password', confirmation_prompt=True)
@with_appcontext
def create_admin(username, email, password):
    """Create a new admin user with USERNAME and EMAIL."""
    from app import db
    from models import User
    if User.query.filter_by(username=username).first():
        raise click.ClickException(f'Username "{username}" already exists.')
    if User.query.filter_by(email=email).first():
        raise click.ClickException(f'Email "{email}" already registered.')
    user = User(username=username, email=email, is_admin=True, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(click.style(f'Admin user "{username}" created (id={user.id}).', fg='green'))


@user_cli.cli.command('promote')
@click.argument('username')
@with_appcontext
def promote(username):
    """Grant admin rights to USERNAME."""
    from app import db
    from models import User
    user = User.query.filter_by(username=username).first()
    if not user:
        raise click.ClickException(f'User "{username}" not found.')
    if user.is_admin:
        click.echo(f'"{username}" is already an admin.')
        return
    user.is_admin = True
    db.session.commit()
    click.echo(click.style(f'"{username}" is now an admin.', fg='green'))


@user_cli.cli.command('demote')
@click.argument('username')
@with_appcontext
def demote(username):
    """Remove admin rights from USERNAME."""
    from app import db
    from models import User
    user = User.query.filter_by(username=username).first()
    if not user:
        raise click.ClickException(f'User "{username}" not found.')
    if not user.is_admin:
        click.echo(f'"{username}" is not an admin.')
        return
    remaining = User.query.filter_by(is_admin=True).count()
    if remaining <= 1:
        raise click.ClickException('Cannot demote the last admin account.')
    user.is_admin = False
    db.session.commit()
    click.echo(click.style(f'Admin rights removed from "{username}".', fg='yellow'))


@user_cli.cli.command('activate')
@click.argument('username')
@with_appcontext
def activate(username):
    """Re-enable a deactivated user account."""
    from app import db
    from models import User
    user = User.query.filter_by(username=username).first()
    if not user:
        raise click.ClickException(f'User "{username}" not found.')
    user.is_active = True
    db.session.commit()
    click.echo(click.style(f'"{username}" has been activated.', fg='green'))


@user_cli.cli.command('deactivate')
@click.argument('username')
@with_appcontext
def deactivate(username):
    """Disable a user account without deleting it."""
    from app import db
    from models import User
    user = User.query.filter_by(username=username).first()
    if not user:
        raise click.ClickException(f'User "{username}" not found.')
    if user.is_admin:
        raise click.ClickException('Cannot deactivate an admin account via CLI.')
    user.is_active = False
    user.is_online = False
    user.session_token = None
    db.session.commit()
    click.echo(click.style(f'"{username}" has been deactivated.', fg='yellow'))
