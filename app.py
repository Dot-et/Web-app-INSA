# app.py - Complete Authentication System with Google OAuth
# Full working version with session tracking

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth
import re
import secrets
import os
from dotenv import load_dotenv

# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================
load_dotenv()

# ============================================
# CREATE FLASK APP
# ============================================
app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# ============================================
# GOOGLE OAUTH CONFIGURATION
# ============================================
# Option 1: Use environment variables (if .env file is working)
# app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
# app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

# Option 2: Hardcode credentials (USE THIS IF .env ISN'T WORKING)
app.config['GOOGLE_CLIENT_ID'] = '555459652773-8414nqlutkscck0pg3dpc734g1f4g3bm.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'

# Print credentials for debugging
print("=" * 60)
print("🔑 Google OAuth Credentials:")
print(f"Client ID: {app.config['GOOGLE_CLIENT_ID']}")
print(f"Client Secret: {app.config['GOOGLE_CLIENT_SECRET'][:15]}...")
print("=" * 60)

# Check if credentials are loaded
if not app.config['GOOGLE_CLIENT_ID'] or not app.config['GOOGLE_CLIENT_SECRET']:
    print("⚠️  WARNING: Google OAuth credentials not found!")
    print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
    print("=" * 60)
else:
    print("✅ Google OAuth credentials loaded successfully!")

# Initialize OAuth
oauth = OAuth(app)

# Register Google OAuth
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# ============================================
# DATABASE SETUP
# ============================================
db = SQLAlchemy(app)

# ============================================
# LOGIN MANAGER SETUP
# ============================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# ============================================
# DATABASE MODELS
# ============================================

class User(UserMixin, db.Model):
    """User model with Google OAuth support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # NULL for Google users
    
    # Google OAuth fields
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    is_google_user = db.Column(db.Boolean, default=False)
    avatar_url = db.Column(db.String(200), nullable=True)
    
    # Security fields
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
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
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
# USER LOADER FOR FLASK-LOGIN
# ============================================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_client_ip():
    """Get client IP address"""
    # Check for proxy headers first
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr or '0.0.0.0'
    return ip

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

# ============================================
# CONTEXT PROCESSOR
# ============================================
@app.context_processor
def inject_user():
    """Make current_user available in all templates"""
    return dict(current_user=current_user)

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

# ============================================
# LOGIN ROUTE (Email/Password)
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with session tracking"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Validate input
        if not email or not password:
            flash('Please fill in all fields', 'danger')
            return render_template('login.html')
        
        # Find user
        user = User.query.filter_by(email=email.lower()).first()
        
        # Check credentials
        if not user or not user.check_password(password):
            # Increment failed attempts for existing user
            if user:
                user.increment_failed_attempts()
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        # Check if account is locked
        if user.is_account_locked():
            flash('Account is locked. Please try again later.', 'danger')
            return render_template('login.html')
        
        # ============================================
        # ✅ SUCCESSFUL LOGIN - CREATE SESSION
        # ============================================
        
        # Get client info
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Reset failed attempts
        user.reset_failed_attempts()
        user.update_last_login(ip_address, user_agent)
        
        # Generate session token
        session_id = generate_session_token()
        
        # Create session record in database
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(user_session)
        db.session.commit()
        
        # Log the user in with Flask-Login
        login_user(user, remember=remember)
        
        # Store session ID in Flask session
        session['_session_id'] = session_id
        
        flash('Login successful!', 'success')
        
        # Redirect to dashboard or next page
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')


# ============================================
# REGISTER ROUTE
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('Please fill in all fields', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            flash(message, 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email.lower()).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email.lower())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


# ============================================
# GOOGLE OAUTH ROUTES
# ============================================

@app.route('/google-login')
def google_login():
    """Redirect to Google for OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/google-callback')
def google_callback():
    """Handle Google OAuth callback with session tracking"""
    try:
        # Get token from Google
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token)
        
        # Extract user data
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        google_id = user_info.get('sub')
        avatar = user_info.get('picture', '')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user with Google
            user = User(
                username=name,
                email=email,
                google_id=google_id,
                is_google_user=True,
                avatar_url=avatar,
                password_hash=None
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully with Google!', 'success')
        else:
            # Update existing user's Google info
            if not user.google_id:
                user.google_id = google_id
                user.is_google_user = True
                user.avatar_url = avatar
                db.session.commit()
            flash('Logged in with Google successfully!', 'success')
        
        # ============================================
        # ✅ GOOGLE LOGIN - CREATE SESSION
        # ============================================
        
        # Get client info
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Update last login
        user.update_last_login(ip_address, user_agent)
        
        # Generate session token
        session_id = generate_session_token()
        
        # Create session record in database
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(user_session)
        db.session.commit()
        
        # Log the user in with Flask-Login
        login_user(user, remember=True)
        
        # Store session ID in Flask session
        session['_session_id'] = session_id
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Google login failed: {str(e)}', 'danger')
        return redirect(url_for('login'))


# ============================================
# DASHBOARD ROUTE
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - protected page"""
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    return render_template('dashboard.html', sessions=sessions)


# ============================================
# SESSIONS MANAGEMENT ROUTES
# ============================================

@app.route('/sessions')
@login_required
def sessions():
    """View and manage all sessions"""
    # Get all sessions for this user (active and inactive)
    all_sessions = UserSession.query.filter_by(
        user_id=current_user.id
    ).order_by(UserSession.created_at.desc()).all()
    
    # Get current session ID from Flask session
    current_session_id = session.get('_session_id')
    
    # Debug: Print to terminal
    print(f"🔍 Found {len(all_sessions)} sessions for user {current_user.id}")
    for s in all_sessions:
        print(f"   Session: {s.id}, Active: {s.is_active}, Device: {s.user_agent[:30] if s.user_agent else 'Unknown'}...")
    
    return render_template('sessions.html', 
                         sessions=all_sessions,
                         current_session_id=current_session_id)


@app.route('/revoke_session/<int:session_id>', methods=['POST'])
@login_required
def revoke_session(session_id):
    """Revoke a specific session"""
    # Find the session
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Cannot revoke current session
    if user_session.session_id == session.get('_session_id'):
        flash('You cannot revoke your current session.', 'warning')
        return redirect(url_for('sessions'))
    
    # Mark session as inactive
    user_session.is_active = False
    db.session.commit()
    
    flash('Session revoked successfully.', 'success')
    return redirect(url_for('sessions'))


# ============================================
# LOGOUT ROUTES
# ============================================

@app.route('/logout')
@login_required
def logout():
    """Logout current user"""
    # Get current session ID
    session_id = session.get('_session_id')
    
    if session_id:
        # Find and deactivate the session
        user_session = UserSession.query.filter_by(
            session_id=session_id,
            user_id=current_user.id
        ).first()
        if user_session:
            user_session.is_active = False
            db.session.commit()
    
    # Logout user
    logout_user()
    session.clear()
    
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/logout_all')
@login_required
def logout_all():
    """Logout from all devices"""
    # Deactivate all sessions for this user
    UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).update({'is_active': False})
    db.session.commit()
    
    # Logout current user
    logout_user()
    session.clear()
    
    flash('Logged out from all devices.', 'info')
    return redirect(url_for('index'))


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


# ============================================
# CREATE DATABASE TABLES
# ============================================

with app.app_context():
    db.create_all()


# ============================================
# RUN THE APP
# ============================================

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🔐 AUTH SYSTEM WITH GOOGLE OAUTH")
    print("=" * 50)
    print("📍 Open: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)