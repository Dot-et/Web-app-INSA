from app import app
from models import db

print('Testing db connection...')
with app.app_context():
    print('Creating tables...')
    db.create_all()
    print('✅ Tables created!')
    print('Tables:', db.metadata.tables.keys())
    
    # Verify users table
    if 'users' in db.metadata.tables:
        print('✅ users table exists!')
    else:
        print('❌ users table missing!')
