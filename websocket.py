from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from models import db, Document, DocumentVersion
from datetime import datetime

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {current_user.username if current_user.is_authenticated else "Anonymous"}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('join_document')
def handle_join_document(data):
    """User joins a document room"""
    doc_id = data.get('doc_id')
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        join_room(room)
        
        # Notify others
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room, include_self=False)

@socketio.on('document_change')
def handle_document_change(data):
    """Handle real-time document changes"""
    doc_id = data.get('doc_id')
    content = data.get('content')
    
    if doc_id and content and current_user.is_authenticated:
        # Update database (auto-save)
        doc = Document.query.get(doc_id)
        if doc:
            doc.content = content
            doc.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Save version
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
                'user': current_user.username
            }, room=room, include_self=False)

@socketio.on('cursor_position')
def handle_cursor_position(data):
    """Track cursor positions for presence"""
    doc_id = data.get('doc_id')
    position = data.get('position')
    
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        emit('cursor_moved', {
            'user': current_user.username,
            'user_id': current_user.id,
            'position': position
        }, room=room, include_self=False)

@socketio.on('leave_document')
def handle_leave_document(data):
    """User leaves a document room"""
    doc_id = data.get('doc_id')
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        leave_room(room)
        emit('user_left', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room)
