from app import app
from app import db
import models

with app.app_context():
    db.create_all()
    print('✅ Tables created successfully!')
    print('Tables:', db.metadata.tables.keys())
