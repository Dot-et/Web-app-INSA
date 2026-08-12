# models.py - Complete Database Models

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
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def increment_failed_attempts(self):
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.is_locked = True
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
    
    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.is_locked = False
        self.locked_until = None
        db.session.commit()
    
    def is_account_locked(self):
        if not self.is_locked:
            return False
        if self.locked_until and datetime.utcnow() > self.locked_until:
            self.is_locked = False
            self.locked_until = None
            db.session.commit()
            return False
        return True
    
    def update_last_login(self, ip_address, user_agent):
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


# ============================================
# DOCUMENT MODELS (For Collaborative Editor)
# ============================================

class Document(db.Model):
    """Document model for collaborative editing"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Relationships
    owner = db.relationship('User', backref='documents_owned', foreign_keys=[owner_id])
    collaborators = db.relationship('DocumentCollaborator', backref='document', lazy=True, cascade='all, delete-orphan')
    versions = db.relationship('DocumentVersion', backref='document', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='document', lazy=True, cascade='all, delete-orphan')


class DocumentCollaborator(db.Model):
    """Document sharing and permissions"""
    __tablename__ = 'document_collaborators'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='viewer')  # viewer, commenter, editor
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='shared_documents')


class DocumentVersion(db.Model):
    """Version history for documents"""
    __tablename__ = 'document_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    version_number = db.Column(db.Integer, nullable=False)
    
    user = db.relationship('User', backref='document_versions')


class Comment(db.Model):
    """Comments on documents"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]))
    # Add to User model in models.py
class User(UserMixin, db.Model):
    # ... existing fields ...
    
    # Subscription fields
    subscription_type = db.Column(db.String(20), default='free')  # free, pro, team
    subscription_end = db.Column(db.DateTime, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    
    def is_premium(self):
        """Check if user has active premium subscription"""
        if self.subscription_type == 'free':
            return False
        
        # Check if subscription is still valid
        if self.subscription_end and datetime.utcnow() > self.subscription_end:
            self.subscription_type = 'free'
            self.subscription_end = None
            db.session.commit()
            return False
        
        return True
    
    def get_document_limit(self):
        """Get document limit based on subscription"""
        if self.is_premium():
            return None  # Unlimited
        return 5  # Free tier: max 5 documents
    
    def can_collaborate(self):
        """Check if user can collaborate"""
        return self.is_premium()
    
    def can_version_history(self):
        """Check if user can access version history"""
        return self.is_premium()
