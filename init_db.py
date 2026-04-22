import os
import sys
import secrets
import string

from app import create_app, db
# Import ALL models so SQLAlchemy's mapper registry is complete before create_all()
from models import User, SiteContent, Page, MenuItem  # noqa: F401


def init_db(admin_password: str | None = None) -> None:
    app = create_app()

    with app.app_context():
        print("Creating database tables…")
        db.create_all()
        print("✅  Database tables created.")

        # ── Admin user ────────────────────────────────────────────────────────
        admin = User.query.filter_by(username='admin').first()

        if not admin:
            # Generate a secure password if one was not supplied
            if not admin_password:
                alphabet = string.ascii_letters + string.digits
                admin_password = ''.join(secrets.choice(alphabet) for _ in range(16))
                generated = True
            else:
                generated = False

            print("\nCreating admin user…")
            admin = User(
                username='admin',
                email='admin@treasurehunt.com',
                is_admin=True,
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()

            print("✅  Admin user created.")
            if generated:
                print(f"\n  Username : admin")
                print(f"  Password : {admin_password}")
                print("\n  ⚠️  Store this password securely — it will not be shown again!")
        else:
            print("\nAdmin user already exists — skipping.")

        print("\n✅  Database initialization complete!")
        print("Run the app with:  python app.py\n")


if __name__ == '__main__':
    # Optionally pass password via env var: ADMIN_PASSWORD=secret python init_db.py
    password = os.environ.get('ADMIN_PASSWORD') or None
    init_db(password)

