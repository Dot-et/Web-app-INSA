# app.py - Complete Flask Application

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth
import re
import secrets
import os
import requests
from dotenv import load_dotenv

# Import from models
from models import db, User, UserSession

# Import routes and websocket
from routes.documents import documents_bp
from websocket import socketio

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

# ============================================
# INITIALIZE DATABASE WITH APP
# ============================================
db.init_app(app)

# ============================================
# GOOGLE OAUTH CONFIGURATION
# ============================================
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

oauth = OAuth(app)

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
# REGISTER BLUEPRINTS
# ============================================
app.register_blueprint(documents_bp, url_prefix='/documents')

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

@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google-callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        headers = {'Authorization': f'Bearer {token["access_token"]}'}
        response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
        
        if response.status_code != 200:
            flash('Failed to get user info from Google', 'danger')
            return redirect(url_for('login'))
        
        user_info = response.json()
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else 'User')
        google_id = user_info.get('sub')
        avatar = user_info.get('picture', '')
        
        if not email:
            flash('Email not found from Google', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
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
            if not user.google_id:
                user.google_id = google_id
                user.is_google_user = True
                user.avatar_url = avatar
                db.session.commit()
            flash('Logged in with Google successfully!', 'success')
        
        login_user(user, remember=True)
        
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
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Google login failed: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    from models import Document
    recent_docs = Document.query.filter_by(owner_id=current_user.id, is_deleted=False).order_by(
        Document.updated_at.desc()
    ).limit(5).all()
    return render_template('dashboard.html', recent_docs=recent_docs)

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
    
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/logout_all')
@login_required
def logout_all():
    UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).update({'is_active': False})
    db.session.commit()
    logout_user()
    session.clear()
    flash('Logged out from all devices.', 'info')
    return redirect(url_for('index'))

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/documents/<int:doc_id>/save', methods=['POST'])
@login_required
def save_document(doc_id):
    """API endpoint for auto-saving documents"""
    from models import Document, DocumentCollaborator
    doc = Document.query.get_or_404(doc_id)
    
    # Check permissions
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator or collaborator.permission not in ['editor', 'commenter']:
            return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if data:
        doc.content = data.get('content', '')
        doc.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'saved'})
    return jsonify({'error': 'No data provided'}), 400

@app.route('/api/documents/<int:doc_id>/rename', methods=['POST'])
@login_required
def rename_document_api(doc_id):
    """API endpoint for renaming documents"""
    from models import Document
    doc = Document.query.get_or_404(doc_id)
    
    if doc.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can rename'}), 403
    
    data = request.get_json()
    if data:
        doc.title = data.get('title', 'Untitled')
        db.session.commit()
        return jsonify({'status': 'renamed'})
    return jsonify({'error': 'No data provided'}), 400

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
# INITIALIZE SOCKETIO
# ============================================

socketio.init_app(app, cors_allowed_origins="*")

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
    print("🔐 AUTH SYSTEM WITH DOCUMENT EDITOR")
    print("=" * 50)
    print("📍 Open: http://127.0.0.1:5000")
    print("📄 Documents: http://127.0.0.1:5000/documents")
    print("=" * 50 + "\n")
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)