# models.py - Authentication System ONLY (Challenge 1)

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import bcrypt

# Create the database object
db = SQLAlchemy()

# ============================================
# USER MODEL
# ============================================

class User(UserMixin, db.Model):
    """User model with Google OAuth support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)
    
    # Google OAuth fields
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    is_google_user = db.Column(db.Boolean, default=False)
    avatar_url = db.Column(db.String(200), nullable=True)
    
    # Security fields
    is_active = db.Column(db.Boolean, default=True)
    failed_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_ip = db.Column(db.String(45), nullable=True)
    last_user_agent = db.Column(db.String(200), nullable=True)
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # ============================================
    # AUTHENTICATION METHODS
    # ============================================
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def increment_failed_attempts(self):
        """Increment failed attempts and lock if needed"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.is_locked = True
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
    
    def reset_failed_attempts(self):
        """Reset failed attempts on successful login"""
        self.failed_attempts = 0
        self.is_locked = False
        self.locked_until = None
        db.session.commit()
    
    def is_account_locked(self):
        """Check if account is locked"""
        if not self.is_locked:
            return False
        if self.locked_until and datetime.utcnow() > self.locked_until:
            self.is_locked = False
            self.locked_until = None
            db.session.commit()
            return False
        return True
    
    def update_last_login(self, ip_address, user_agent):
        """Update last login info"""
        self.last_login = datetime.utcnow()
        self.last_ip = ip_address
        self.last_user_agent = user_agent
        db.session.commit()


# ============================================
# USER SESSION MODEL
# ============================================

class UserSession(db.Model):
    """Track user sessions"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, session_id, user_id, ip_address=None, user_agent=None):
        self.session_id = session_id
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.expires_at = datetime.utcnow() + timedelta(days=7)