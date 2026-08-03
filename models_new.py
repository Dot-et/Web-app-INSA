
# ============================================
# DOCUMENT EDITOR MODELS
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'owner': self.owner.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'collaborators': [c.user.username for c in self.collaborators]
        }

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
