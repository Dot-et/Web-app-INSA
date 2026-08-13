from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from models import db, Document, DocumentVersion
from datetime import datetime

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        print(f'✅ Client connected: {current_user.username}')
    else:
        print('👤 Anonymous client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f'❌ Client disconnected: {current_user.username}')

@socketio.on('join_document')
def handle_join_document(data):
    """User joins a document room"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        join_room(room)
        print(f'📄 {current_user.username} joined document {doc_id}')
        
        # Notify other users
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id,
            'avatar': current_user.username[0].upper()
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

@socketio.on('document_change')
def handle_document_change(data):
    """Handle real-time document changes"""
    doc_id = data.get('doc_id')
    content = data.get('content')
    
    if doc_id and content and current_user.is_authenticated:
        try:
            print(f'📝 Document change from {current_user.username}, doc: {doc_id}')
            
            # Save to database
            doc = Document.query.get(doc_id)
            if doc:
                doc.content = content
                doc.updated_at = datetime.utcnow()
                db.session.commit()
                print(f'✅ Saved to database')
                
                # Broadcast to all users EXCEPT the sender
                room = f'doc_{doc_id}'
                emit('document_updated', {
                    'content': content,
                    'user': current_user.username,
                    'user_id': current_user.id
                }, room=room, include_self=False)
                
                print(f'📤 Broadcasted to room: {room}')
                
        except Exception as e:
            print(f'⚠️ Error saving document: {e}')
            emit('error', {'message': 'Failed to save document'})

# ============================================
# BONUS: CURSOR TRACKING
# ============================================

@socketio.on('cursor_move')
def handle_cursor_move(data):
    """Handle cursor position updates"""
    doc_id = data.get('doc_id')
    index = data.get('index')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('cursor_update', {
            'user': current_user.username,
            'user_id': current_user.id,
            'index': index
        }, room=room, include_self=False)

# ============================================
# BONUS: TYPING INDICATORS
# ============================================

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('user_typing', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator"""
    doc_id = data.get('doc_id')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('user_stop_typing', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room, include_self=False)