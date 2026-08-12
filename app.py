# app.py - Authentication System ONLY (Challenge 1)

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth
import re
import secrets
import os
import requests
from dotenv import load_dotenv
import bcrypt
import string

# Import from models
from models import db, User, UserSession

# Load environment variables
load_dotenv()

# ============================================
# CREATE FLASK APP
# ============================================
app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

# ============================================
# INITIALIZE DATABASE WITH APP
# ============================================
db.init_app(app)

# ============================================
# OAUTH CONFIGURATION - FIXED
# ============================================
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',  # ADD THIS LINE
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# ============================================
# LOGIN MANAGER SETUP
# ============================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# ============================================
# USER LOADER
# ============================================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr or '0.0.0.0'
    return ip

def generate_session_token():
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
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
    return dict(current_user=current_user)

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not email or not password:
            flash('Please fill in all fields', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user or not user.check_password(password):
            if user:
                user.increment_failed_attempts()
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        if user.is_account_locked():
            flash('Account is locked. Please try again later.', 'danger')
            return render_template('login.html')
        
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        user.reset_failed_attempts()
        user.update_last_login(ip_address, user_agent)
        
        session_id = generate_session_token()
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(user_session)
        db.session.commit()
        
        login_user(user, remember=remember)
        session['_session_id'] = session_id
        
        flash('Login successful!', 'success')
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
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

@app.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    redirect_uri = 'http://127.0.0.1:4000/callback'
    print(f"🔑 Redirect URI: {redirect_uri}")
    
    try:
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        print(f"❌ OAuth Error: {e}")
        flash('Failed to initiate Google login. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/callback')
def google_callback():
    """Handle the callback from Google after authorization"""
    try:
        # Get the access token
        token = google.authorize_access_token()
        print(f"✅ Token received: {token.keys()}")
        
        # Get user info using the access token
        resp = requests.get(
            'https://openidconnect.googleapis.com/v1/userinfo',
            headers={'Authorization': f'Bearer {token["access_token"]}'}
        )
        
        if resp.status_code != 200:
            flash('Failed to get user info from Google', 'danger')
            return redirect(url_for('login'))
        
        userinfo = resp.json()
        email = userinfo.get('email')
        name = userinfo.get('name', 'Google User')
        picture = userinfo.get('picture', None)
        google_id = userinfo.get('sub')
        
        print(f"👤 User email: {email}")
        print(f"👤 User name: {name}")
        
        if not email:
            flash('Email not found from Google', 'danger')
            return redirect(url_for('login'))
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Generate random password for Google users
            alphabet = string.ascii_letters + string.digits
            random_password = ''.join(secrets.choice(alphabet) for _ in range(32))
            hashed_password = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt())
            
            # Create new user
            user = User(
                username=email.split('@')[0],
                email=email,
                password_hash=hashed_password.decode('utf-8'),
                google_id=google_id
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully with Google!', 'success')
        else:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
                db.session.commit()
            flash(f'Welcome back, {name}!', 'success')
        
        # Log the user in
        login_user(user, remember=True)
        
        # Create session entry
        session_id = generate_session_token()
        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(user_session)
        db.session.commit()
        
        session['_session_id'] = session_id
        user.update_last_login(ip_address, user_agent)
        
        flash(f'Welcome, {name}!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"❌ Google OAuth error: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/sessions')
@login_required
def sessions():
    all_sessions = UserSession.query.filter_by(
        user_id=current_user.id
    ).order_by(UserSession.created_at.desc()).all()
    current_session_id = session.get('_session_id')
    return render_template('sessions.html', 
                         sessions=all_sessions,
                         current_session_id=current_session_id)

@app.route('/revoke_session/<int:session_id>', methods=['POST'])
@login_required
def revoke_session(session_id):
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()
    
    if user_session.session_id == session.get('_session_id'):
        flash('You cannot revoke your current session.', 'warning')
        return redirect(url_for('sessions'))
    
    user_session.is_active = False
    db.session.commit()
    flash('Session revoked successfully.', 'success')
    return redirect(url_for('sessions'))

@app.route('/logout')
@login_required
def logout():
    session_id = session.get('_session_id')
    if session_id:
        user_session = UserSession.query.filter_by(
            session_id=session_id,
            user_id=current_user.id
        ).first()
        if user_session:
            user_session.is_active = False
            db.session.commit()
    
    session.clear()
    logout_user()
    flash('You have been logged out.', 'info')
    response = redirect(url_for('index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/logout_all')
@login_required
def logout_all():
    UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).update({'is_active': False})
    db.session.commit()
    session.clear()
    logout_user()
    flash('Logged out from all devices.', 'info')
    response = redirect(url_for('index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
    print("✅ Database tables created!")
    print("Tables:", db.metadata.tables.keys())

# ============================================
# RUN THE APP
# ============================================

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🔐 AUTHENTICATION SYSTEM")
    print("=" * 50)
    print("📍 Open: http://127.0.0.1:4000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=4000)