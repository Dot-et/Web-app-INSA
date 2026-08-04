# websocket.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from models import db, Document, DocumentVersion
from datetime import datetime

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f'✅ Client connected: {current_user.username}')

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        print(f'❌ Client disconnected: {current_user.username}')

@socketio.on('join_document')
def handle_join_document(data):
    doc_id = data.get('doc_id')
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        join_room(room)
        print(f'📄 {current_user.username} joined document {doc_id}')
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room, include_self=False)

@socketio.on('leave_document')
def handle_leave_document(data):
    doc_id = data.get('doc_id')
    if doc_id and current_user.is_authenticated:
        room = f'doc_{doc_id}'
        leave_room(room)
        emit('user_left', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room)

@socketio.on('document_change')
def handle_document_change(data):
    doc_id = data.get('doc_id')
    content = data.get('content')
    
    if doc_id and content and current_user.is_authenticated:
        doc = Document.query.get(doc_id)
        if doc:
            doc.content = content
            doc.updated_at = datetime.utcnow()
            db.session.commit()
            
            room = f'doc_{doc_id}'
            emit('document_updated', {
                'content': content,
                'user': current_user.username
            }, room=room, include_self=False)