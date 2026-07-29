
# This file defines how data is stored in the database

from flask_sqlalchemy import SQLAlchemy
# SQLAlchemy is an ORM (Object Relational Mapper)
# It lets us work with databases using Python objects instead of SQL queries

from flask_login import UserMixin
# UserMixin provides default implementations for Flask-Login
# It gives us methods like is_authenticated, is_active, etc.

from datetime import datetime, timedelta
# datetime: For working with dates and times
# timedelta: For calculating time differences (like "30 minutes from now")

import bcrypt
# bcrypt: Library for hashing passwords securely

# Create the database object
# This will be used to define models and interact with the database
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User Model - Represents a user account in the database
    
    UserMixin: Provides default implementations for Flask-Login
    db.Model: Makes this class a database table
    
    Think of this as a blueprint for a "users" table in your database.
    Each user will be a row in this table.
    """
    
    # Set the table name (optional, but good practice)
    __tablename__ = 'users'
    
    # Define columns (fields) for the users table
    
    # id: Primary key - unique identifier for each user
    # db.Integer: This is a whole number
    # primary_key=True: This field uniquely identifies each record
    id = db.Column(db.Integer, primary_key=True)
    
    # email: User's email address
    # db.String(120): Text field with maximum 120 characters
    # unique=True: No two users can have the same email
    # nullable=False: This field is required (can't be empty)
    # index=True: Creates an index for faster searches
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # username: User's display name
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    
    # password_hash: Stores the hashed password (never store plain text!)
    # nullable=True: Can be null for Google OAuth users (they don't have a password)
    password_hash = db.Column(db.String(128), nullable=True)
    
    # is_google_user: True if user registered with Google
    # db.Boolean: True/False value
    is_google_user = db.Column(db.Boolean, default=False)
    
    # google_id: Unique ID from Google for OAuth users
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    
    # Security fields
    
    # is_active: Can this user log in?
    # Default is True - user is active by default
    is_active = db.Column(db.Boolean, default=True)
    
    # is_locked: Is the account temporarily locked?
    # Used when someone tries too many wrong passwords
    is_locked = db.Column(db.Boolean, default=False)
    
    # locked_until: When does the lock expire?
    # If None, the account isn't locked
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # failed_login_attempts: How many wrong password attempts
    # Increments when someone enters wrong password
    failed_login_attempts = db.Column(db.Integer, default=0)
    
    # Account tracking
    
    # created_at: When was this account created?
    # datetime.utcnow: Gets current UTC time (timezone-independent)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # last_login: When did the user last log in?
    last_login = db.Column(db.DateTime, nullable=True)
    
    # last_ip: What IP address did they use last?
    # String(45): Can store IPv6 addresses (longer than IPv4)
    last_ip = db.Column(db.String(45), nullable=True)
    
    # last_user_agent: What browser/device did they use?
    last_user_agent = db.Column(db.String(200), nullable=True)
    
    # Relationships - Link to other tables
    
    # sessions: All sessions this user has
    # db.relationship: Creates a virtual connection to UserSession table
    # backref='user': UserSession can access the user via .user
    # lazy=True: Loads data when accessed
    # cascade='all, delete-orphan': If user is deleted, their sessions are too
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # login_history: All login attempts for this user
    login_history = db.relationship('LoginHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """
        Hash and store a password securely
        
        Why hash? 
        - If someone steals the database, they can't read passwords
        - bcrypt is designed to be slow (makes brute force attacks harder)
        - Each hash uses a unique salt (extra security)
        """
        # gensalt(): Generates a random salt (extra security)
        salt = bcrypt.gensalt()
        
        # hashpw: Hashes the password with the salt
        # .encode('utf-8'): Converts string to bytes (bcrypt needs bytes)
        # .decode('utf-8'): Converts back to string for storage
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """
        Check if a provided password matches the stored hash
        
        Returns True if password is correct, False otherwise
        """
        # If no password hash exists (Google OAuth user), they can't use password login
        if not self.password_hash:
            return False
        
        # checkpw: Compares the provided password with stored hash
        # Returns True if they match, False otherwise
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def increment_failed_attempts(self):
        """
        Increase the failed login counter
        If it reaches 5, lock the account for 30 minutes
        """
        # Add 1 to the counter
        self.failed_login_attempts += 1
        
        # If they've failed 5 or more times
        if self.failed_login_attempts >= 5:
            # Lock the account
            self.is_locked = True
            
            # Set lock expiration to 30 minutes from now
            # timedelta(minutes=30): Represents 30 minutes
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        # Save changes to database
        db.session.commit()
    
    def reset_failed_attempts(self):
        """
        Reset the failed login counter
        Called when a user successfully logs in
        """
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_until = None
        db.session.commit()
    
    def is_account_locked(self):
        """
        Check if the account is currently locked
        
        Returns True if locked, False otherwise
        """
        # If not locked, return False
        if not self.is_locked:
            return False
        
        # If there's a lock expiration time
        if self.locked_until and datetime.utcnow() > self.locked_until:
            # The lock has expired, so unlock the account
            self.is_locked = False
            self.locked_until = None
            db.session.commit()
            return False
        
        # Account is still locked
        return True
    
    def update_last_login(self, ip_address, user_agent):
        """
        Update login tracking information
        Called when a user successfully logs in
        """
        self.last_login = datetime.utcnow()
        self.last_ip = ip_address
        self.last_user_agent = user_agent
        db.session.commit()
    
    def __repr__(self):
        """
        String representation of the user (used for debugging)
        """
        return f'<User {self.email}>'


class UserSession(db.Model):
    """
    UserSession Model - Tracks active user sessions
    
    Each time a user logs in, we create a session record.
    This allows users to see and manage their active sessions.
    """
    
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # session_id: Unique identifier for this session
    # This is stored in the user's browser cookie
    session_id = db.Column(db.String(128), unique=True, nullable=False)
    
    # user_id: Foreign key linking to the User table
    # db.ForeignKey: Links to the 'id' column in 'users' table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Session details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # expires_at: When does this session expire?
    # Sessions expire after 7 days by default
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # ip_address: IP address used for this session
    ip_address = db.Column(db.String(45), nullable=True)
    
    # user_agent: Browser/device information
    user_agent = db.Column(db.String(200), nullable=True)
    
    # device_name: Human-readable device name
    # Example: "Windows (Chrome)", "iPhone", "Android Phone"
    device_name = db.Column(db.String(100), nullable=True)
    
    # is_active: Is this session still active?
    is_active = db.Column(db.Boolean, default=True)
    
    # Suspicious activity
    is_suspicious = db.Column(db.Boolean, default=False)
    suspicion_reason = db.Column(db.String(200), nullable=True)
    
    def __init__(self, session_id, user_id, ip_address=None, user_agent=None):
        """
        Constructor - Called when creating a new session
        
        session_id: Unique session token
        user_id: ID of the user
        ip_address: IP address from request
        user_agent: Browser/device info from request
        """
        self.session_id = session_id
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        
        # Set expiration to 7 days from now
        self.expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Try to determine device name from user agent
        if user_agent:
            self.device_name = self._parse_user_agent(user_agent)
    
    def _parse_user_agent(self, user_agent_string):
        """
        Parse user agent string to get a human-readable device name
        
        This is a simple implementation - you can make it more sophisticated
        """
        # Check if it's a mobile device
        if 'Mobile' in user_agent_string:
            # Check if it's an iPhone
            if 'iPhone' in user_agent_string:
                return 'iPhone'
            # Check if it's an Android phone
            elif 'Android' in user_agent_string:
                return 'Android Phone'
            # Other mobile device
            else:
                return 'Mobile Device'
        
        # Check for Windows
        elif 'Windows' in user_agent_string:
            if 'Chrome' in user_agent_string:
                return 'Windows (Chrome)'
            elif 'Firefox' in user_agent_string:
                return 'Windows (Firefox)'
            elif 'Edge' in user_agent_string:
                return 'Windows (Edge)'
            else:
                return 'Windows'
        
        # Check for Mac
        elif 'Macintosh' in user_agent_string:
            return 'Mac'
        
        # Check for Linux
        elif 'Linux' in user_agent_string:
            return 'Linux'
        
        # Unknown device
        else:
            return 'Unknown Device'
    
    def is_expired(self):
        """
        Check if this session has expired
        
        Returns True if expired, False otherwise
        """
        # Get current UTC time and compare with expiration time
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, days=7):
        """
        Extend the session expiration date
        
        This is called when a user is active and we want to keep their session alive
        """
        # Add the specified number of days to expiration
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        db.session.commit()


class LoginHistory(db.Model):
    """
    LoginHistory Model - Records all login attempts
    
    This provides an audit trail for security purposes.
    We track both successful and failed attempts.
    """
    
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # user_id: Link to the User table
    # Can be null for failed attempts where the email doesn't exist
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # email: The email used for login
    # Stored separately so we can track failed attempts even if the email doesn't exist
    email = db.Column(db.String(120), nullable=True)
    
    # Login details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    
    # success: Was this login attempt successful?
    success = db.Column(db.Boolean, default=False)
    
    # reason: Why did it fail? Or why was it marked suspicious?
    reason = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        status = 'SUCCESS' if self.success else 'FAILED'
        return f'<LoginHistory {self.email} - {status}>'