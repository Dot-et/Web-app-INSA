from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Document, DocumentCollaborator, DocumentVersion, Comment
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

# ============================================
# DOCUMENT MANAGEMENT ROUTES
# ============================================

@documents_bp.route('/')
@login_required
def list_documents():
    owned = Document.query.filter_by(owner_id=current_user.id, is_deleted=False).all()
    shared = Document.query.join(DocumentCollaborator).filter(
        DocumentCollaborator.user_id == current_user.id
    ).all()
    return render_template('documents.html', owned=owned, shared=shared)


@documents_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_document():
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
    doc = Document.query.get_or_404(doc_id)
    
    # Check access
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator:
            flash('You don\'t have access to this document.', 'danger')
            return redirect(url_for('documents.list_documents'))
    
    comments = Comment.query.filter_by(document_id=doc_id, parent_id=None).order_by(
        Comment.created_at.asc()
    ).all()
    
    return render_template('editor.html', document=doc, comments=comments)


@documents_bp.route('/<int:doc_id>/rename', methods=['POST'])
@login_required
def rename_document(doc_id):
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


# ============================================
# SHARING ROUTES
# ============================================

@documents_bp.route('/<int:doc_id>/share', methods=['GET', 'POST'])
@login_required
def share_document(doc_id):
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


@documents_bp.route('/<int:doc_id>/collaborators/<int:collab_id>/remove', methods=['POST'])
@login_required
def remove_collaborator(doc_id, collab_id):
    """Remove a collaborator from a document"""
    doc = Document.query.get_or_404(doc_id)
    
    # Only owner can remove collaborators
    if doc.owner_id != current_user.id:
        flash('Only the owner can remove collaborators.', 'danger')
        return redirect(url_for('documents.share_document', doc_id=doc_id))
    
    collaborator = DocumentCollaborator.query.get_or_404(collab_id)
    
    # Don't remove the owner
    if collaborator.user_id == doc.owner_id:
        flash('Cannot remove the document owner.', 'warning')
        return redirect(url_for('documents.share_document', doc_id=doc_id))
    
    db.session.delete(collaborator)
    db.session.commit()
    flash('Collaborator removed successfully.', 'success')
    return redirect(url_for('documents.share_document', doc_id=doc_id))


# ============================================
# VERSION HISTORY ROUTES
# ============================================

@documents_bp.route('/<int:doc_id>/versions')
@login_required
def view_versions(doc_id):
    doc = Document.query.get_or_404(doc_id)
    versions = DocumentVersion.query.filter_by(document_id=doc_id).order_by(
        DocumentVersion.created_at.desc()
    ).all()
    return render_template('versions.html', document=doc, versions=versions)


@documents_bp.route('/<int:doc_id>/versions/<int:version_id>/restore', methods=['POST'])
@login_required
def restore_version(doc_id, version_id):
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


# ============================================
# COMMENTS ROUTES
# ============================================

@documents_bp.route('/<int:doc_id>/comments', methods=['POST'])
@login_required
def add_comment(doc_id):
    doc = Document.query.get_or_404(doc_id)
    
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator or collaborator.permission == 'viewer':
            flash('You don\'t have permission to comment.', 'danger')
            return redirect(url_for('documents.edit_document', doc_id=doc_id))
    
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')
    
    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('documents.edit_document', doc_id=doc_id))
    
    comment = Comment(
        document_id=doc_id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id if parent_id else None
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=doc_id))


@documents_bp.route('/comments/<int:comment_id>/resolve', methods=['POST'])
@login_required
def resolve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    doc = Document.query.get(comment.document_id)
    
    if comment.user_id != current_user.id and doc.owner_id != current_user.id:
        flash('You cannot resolve this comment.', 'danger')
        return redirect(url_for('documents.edit_document', doc_id=comment.document_id))
    
    comment.resolved = True
    db.session.commit()
    flash('Comment resolved!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=comment.document_id))


@documents_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        flash('You cannot delete this comment.', 'danger')
        return redirect(url_for('documents.edit_document', doc_id=comment.document_id))
    
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted!', 'success')
    return redirect(url_for('documents.edit_document', doc_id=comment.document_id))


# ============================================
# API ROUTES
# ============================================

@documents_bp.route('/<int:doc_id>/api/save', methods=['POST'])
@login_required
def api_save_document(doc_id):
    """API endpoint for auto-saving documents"""
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


@documents_bp.route('/<int:doc_id>/api/rename', methods=['POST'])
@login_required
def api_rename_document(doc_id):
    """API endpoint for renaming documents"""
    doc = Document.query.get_or_404(doc_id)
    
    if doc.owner_id != current_user.id:
        return jsonify({'error': 'Only the owner can rename'}), 403
    
    data = request.get_json()
    if data:
        doc.title = data.get('title', 'Untitled')
        db.session.commit()
        return jsonify({'status': 'renamed'})
    return jsonify({'error': 'No data provided'}), 400


@documents_bp.route('/<int:doc_id>/api/content', methods=['GET'])
@login_required
def api_get_content(doc_id):
    """API endpoint to fetch document content"""
    doc = Document.query.get_or_404(doc_id)
    
    # Check access
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator:
            return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'content': doc.content,
        'title': doc.title,
        'updated_at': doc.updated_at.isoformat()
    })


@documents_bp.route('/<int:doc_id>/api/versions', methods=['GET'])
@login_required
def api_get_versions(doc_id):
    """API endpoint to fetch version history"""
    doc = Document.query.get_or_404(doc_id)
    
    # Check access
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator:
            return jsonify({'error': 'Access denied'}), 403
    
    versions = DocumentVersion.query.filter_by(document_id=doc_id).order_by(
        DocumentVersion.created_at.desc()
    ).limit(50).all()
    
    return jsonify([{
        'id': v.id,
        'version_number': v.version_number,
        'username': v.user.username if v.user else 'Unknown',
        'created_at': v.created_at.isoformat(),
        'preview': v.content[:150] if v.content else ''
    } for v in versions])


@documents_bp.route('/<int:doc_id>/api/comments', methods=['GET'])
@login_required
def api_get_comments(doc_id):
    """API endpoint to fetch comments"""
    doc = Document.query.get_or_404(doc_id)
    
    # Check access
    if doc.owner_id != current_user.id:
        collaborator = DocumentCollaborator.query.filter_by(
            document_id=doc_id, user_id=current_user.id
        ).first()
        if not collaborator:
            return jsonify({'error': 'Access denied'}), 403
    
    comments = Comment.query.filter_by(
        document_id=doc_id, parent_id=None
    ).order_by(Comment.created_at.asc()).all()
    
    def format_comment(comment):
        return {
            'id': comment.id,
            'content': comment.content,
            'username': comment.user.username if comment.user else 'Unknown',
            'user_id': comment.user_id,
            'created_at': comment.created_at.isoformat(),
            'resolved': comment.resolved,
            'replies': [format_comment(reply) for reply in comment.replies]
        }
    
    return jsonify([format_comment(c) for c in comments])