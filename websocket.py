# websocket.py - Complete Real-time WebSocket Handlers

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from models import db, Document, DocumentVersion
from datetime import datetime

# Initialize SocketIO with CORS support
socketio = SocketIO(cors_allowed_origins="*")

# ============================================
# CONNECTION HANDLERS
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        print(f'✅ Client connected: {current_user.username}')
        emit('connection_status', {
            'status': 'connected',
            'user': current_user.username
        })
    else:
        print('👤 Anonymous client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f'❌ Client disconnected: {current_user.username}')

# ============================================
# DOCUMENT ROOM HANDLERS
# ============================================

@socketio.on('join_document')
def handle_join_document(data):
    """User joins a document room"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        join_room(room)
        
        print(f'📄 {current_user.username} joined document {doc_id}')
        
        # Notify other users in the room
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id,
            'avatar': current_user.avatar_url or current_user.username[0].upper()
        }, room=room, include_self=False)

@socketio.on('leave_document')
def handle_leave_document(data):
    """User leaves a document room"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        leave_room(room)
        
        print(f'👋 {current_user.username} left document {doc_id}')
        
        # Notify other users
        emit('user_left', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room)

# ============================================
# DOCUMENT CONTENT HANDLERS
# ============================================

@socketio.on('document_change')
def handle_document_change(data):
    """Handle real-time document changes"""
    doc_id = data.get('doc_id')
    content = data.get('content')
    
    if doc_id and content and current_user.is_authenticated:
        try:
            # Update database (auto-save)
            doc = Document.query.get(doc_id)
            if doc:
                doc.content = content
                doc.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Save version history
                version_count = DocumentVersion.query.filter_by(document_id=doc_id).count()
                version = DocumentVersion(
                    document_id=doc_id,
                    content=content,
                    user_id=current_user.id,
                    version_number=version_count + 1
                )
                db.session.add(version)
                db.session.commit()
                
                # Broadcast to all users in the room
                room = f'doc_{doc_id}'
                emit('document_updated', {
                    'content': content,
                    'user': current_user.username,
                    'user_id': current_user.id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room, include_self=False)
                
        except Exception as e:
            print(f'⚠️ Error saving document: {e}')
            emit('error', {'message': 'Failed to save document'}, room=room)

# ============================================
# CURSOR TRACKING HANDLERS
# ============================================

@socketio.on('cursor_update')
def handle_cursor_update(data):
    """Handle cursor position updates for live tracking"""
    doc_id = data.get('doc_id')
    cursor_position = data.get('position')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('cursor_update', {
            'user': current_user.username,
            'user_id': current_user.id,
            'position': cursor_position,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room, include_self=False)

@socketio.on('selection_update')
def handle_selection_update(data):
    """Handle text selection updates"""
    doc_id = data.get('doc_id')
    selection = data.get('selection')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('selection_update', {
            'user': current_user.username,
            'user_id': current_user.id,
            'selection': selection
        }, room=room, include_self=False)

# ============================================
# TYPING INDICATORS
# ============================================

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('user_typing', {
            'user': current_user.username,
            'user_id': current_user.id,
            'is_typing': True
        }, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('user_typing', {
            'user': current_user.username,
            'user_id': current_user.id,
            'is_typing': False
        }, room=room, include_self=False)

# ============================================
# COMMENT HANDLERS (Real-time Comments)
# ============================================

@socketio.on('new_comment')
def handle_new_comment(data):
    """Handle new comment in real-time"""
    doc_id = data.get('doc_id')
    comment_id = data.get('comment_id')
    content = data.get('content')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('comment_added', {
            'user': current_user.username,
            'user_id': current_user.id,
            'comment_id': comment_id,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room, include_self=False)

@socketio.on('resolve_comment')
def handle_resolve_comment(data):
    """Handle comment resolution in real-time"""
    doc_id = data.get('doc_id')
    comment_id = data.get('comment_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('comment_resolved', {
            'user': current_user.username,
            'user_id': current_user.id,
            'comment_id': comment_id
        }, room=room, include_self=False)

# ============================================
# ERROR HANDLING
# ============================================

@socketio.on_error()
def handle_socket_error(e):
    """Handle socket errors"""
    print(f'⚠️ Socket error: {e}')
    emit('error', {'message': 'An error occurred'})

# ============================================
# PING/PONG (Keep Connection Alive)
# ============================================

@socketio.on('ping')
def handle_ping():
    """Handle ping to keep connection alive"""
    emit('pong', {'timestamp': datetime.utcnow().isoformat()})