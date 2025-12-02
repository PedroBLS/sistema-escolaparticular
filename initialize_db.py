from app import create_app, db
from app.models import User

def initialize_database():
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(email='admin@escola.com').first():
            admin = User(
                email='admin@escola.com',
                nome='Administrador',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")

if __name__ == '__main__':
    initialize_database()