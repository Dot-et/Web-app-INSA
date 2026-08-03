from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Document, DocumentCollaborator, DocumentVersion, Comment
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/')
@login_required
def list_documents():
    """Show user's documents"""
    owned = Document.query.filter_by(owner_id=current_user.id, is_deleted=False).all()
    shared = Document.query.join(DocumentCollaborator).filter(
        DocumentCollaborator.user_id == current_user.id
    ).all()
    return render_template('documents.html', owned=owned, shared=shared)

@documents_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_document():
    """Create a new document"""
    if request.method == 'POST':
        title = request.form.get('title', 'Untitled')
        doc = Document(title=title, owner_id=current_user.id, content='')
        db.session.add(doc)
        db.session.commit()
        flash('Document created!', 'success')
        return redirect(url_for('documents.edit_document', doc_id=doc.id))
    return render_template('create_document.html')

@documents_bp.route('/<int:doc_id>')
@login_required
def edit_document(doc_id):
    """Edit a document"""
    doc = Document.query.get_or_404(doc_id)
    # Check permissions
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator:
            flash('You don\'t have access to this document.', 'danger')
            return redirect(url_for('documents.list_documents'))
    return render_template('editor.html', document=doc)

@documents_bp.route('/<int:doc_id>/rename', methods=['POST'])
@login_required
def rename_document(doc_id):
    """Rename a document"""
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        flash('Only the owner can rename this document.', 'danger')
        return redirect(url_for('documents.list_documents'))
    
    new_title = request.form.get('title')
    if new_title:
        doc.title = new_title
        db.session.commit()
        flash('Document renamed!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=doc_id))

@documents_bp.route('/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Soft delete a document"""
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        flash('Only the owner can delete this document.', 'danger')
        return redirect(url_for('documents.list_documents'))
    
    doc.is_deleted = True
    db.session.commit()
    flash('Document deleted!', 'success')
    return redirect(url_for('documents.list_documents'))

@documents_bp.route('/<int:doc_id>/duplicate', methods=['POST'])
@login_required
def duplicate_document(doc_id):
    """Duplicate a document"""
    original = Document.query.get_or_404(doc_id)
    new_doc = Document(
        title=f"{original.title} (Copy)",
        owner_id=current_user.id,
        content=original.content
    )
    db.session.add(new_doc)
    db.session.commit()
    flash('Document duplicated!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=new_doc.id))

@documents_bp.route('/<int:doc_id>/share', methods=['GET', 'POST'])
@login_required
def share_document(doc_id):
    """Share document with other users"""
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        flash('Only the owner can share this document.', 'danger')
        return redirect(url_for('documents.list_documents'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        permission = request.form.get('permission', 'viewer')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('User not found.', 'danger')
        elif user.id == current_user.id:
            flash('You cannot share with yourself.', 'warning')
        else:
            existing = DocumentCollaborator.query.filter_by(
                document_id=doc_id, user_id=user.id
            ).first()
            if existing:
                existing.permission = permission
            else:
                collab = DocumentCollaborator(
                    document_id=doc_id, user_id=user.id, permission=permission
                )
                db.session.add(collab)
            db.session.commit()
            flash(f'Document shared with {user.username} as {permission}!', 'success')
    
    collaborators = DocumentCollaborator.query.filter_by(document_id=doc_id).all()
    return render_template('share.html', document=doc, collaborators=collaborators)

@documents_bp.route('/<int:doc_id>/versions')
@login_required
def view_versions(doc_id):
    """View document version history"""
    doc = Document.query.get_or_404(doc_id)
    versions = DocumentVersion.query.filter_by(document_id=doc_id).order_by(
        DocumentVersion.created_at.desc()
    ).all()
    return render_template('versions.html', document=doc, versions=versions)

@documents_bp.route('/<int:doc_id>/versions/<int:version_id>/restore', methods=['POST'])
@login_required
def restore_version(doc_id, version_id):
    """Restore a previous version"""
    doc = Document.query.get_or_404(doc_id)
    version = DocumentVersion.query.get_or_404(version_id)
    
    if doc.owner_id != current_user.id:
        flash('Only the owner can restore versions.', 'danger')
        return redirect(url_for('documents.list_documents'))
    
    doc.content = version.content
    doc.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Version restored!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=doc_id))

@documents_bp.route('/<int:doc_id>/comments', methods=['POST'])
@login_required
def add_comment(doc_id):
    """Add a comment to a document"""
    doc = Document.query.get_or_404(doc_id)
    content = request.form.get('content')
    
    if content:
        comment = Comment(
            document_id=doc_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=doc_id))

@documents_bp.route('/comments/<int:comment_id>/resolve', methods=['POST'])
@login_required
def resolve_comment(comment_id):
    """Resolve a comment"""
    comment = Comment.query.get_or_404(comment_id)
    comment.resolved = True
    db.session.commit()
    flash('Comment resolved!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=comment.document_id))
