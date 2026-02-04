from app import create_app, db
from models import User

def init_db():
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Create admin user
            print("\nCreating admin user...")
            admin = User(
                username='admin',
                email='admin@treasurehunt.com',
                is_admin=True
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("Admin user created successfully!")
            print("\nAdmin Credentials:")
            print("Username: admin")
            print("Password: admin123")
            print("\n⚠️  IMPORTANT: Please change the admin password after first login!")
        else:
            print("\nAdmin user already exists.")
        
        print("\n✅ Database initialization complete!")
        print("\nYou can now run the application with: uv run python app.py")

if __name__ == '__main__':
    init_db()
