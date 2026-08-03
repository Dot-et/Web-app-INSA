/* ============================================
   MAIN APP
   ============================================ */

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize editor
    const editorContainer = document.getElementById('editor-container');
    if (editorContainer) {
        const docId = parseInt(editorContainer.dataset.docId);
        const userId = parseInt(editorContainer.dataset.userId);
        const username = editorContainer.dataset.username;
        const initialContent = editorContainer.dataset.content || '';
        
        // Initialize editor
        const quill = initEditor('#editor-container', {
            docId: docId,
            userId: userId,
            username: username,
            content: initialContent,
            placeholder: 'Start writing your document...'
        });
        
        // Initialize auto-save
        initAutoSave(quill, docId, {
            onSaveStart: function() {
                setStatus('saving', 'Saving...');
            },
            onSaveEnd: function() {
                setStatus('', 'Saved');
                updateLastSaved();
            },
            onError: function() {
                setStatus('', 'Error saving');
            }
        });
        
        // Initialize shortcuts
        initShortcuts({
            save: function() {
                const content = getEditorContent();
                saveDocument(docId, content, function() {
                    setStatus('', 'Saved');
                    updateLastSaved();
                    showNotification('Document saved! ✅');
                });
            },
            bold: function() {
                document.querySelector('.ql-bold')?.click();
            },
            italic: function() {
                document.querySelector('.ql-italic')?.click();
            },
            underline: function() {
                document.querySelector('.ql-underline')?.click();
            },
            versions: function() {
                window.location.href = '/documents/' + docId + '/versions';
            }
        });
        
        // Initialize socket
        initSocket({
            onConnect: function() {
                joinDocumentRoom(docId);
            },
            onDocumentUpdate: function(data) {
                const currentContent = getEditorContent();
                if (data.content !== currentContent) {
                    setEditorContent(data.content);
                    updateWordCount(quill, 'wordCount');
                    showNotification('✏️ Updated by ' + data.user);
                }
            },
            onUserJoined: function(data) {
                addPresenceUser(data);
            },
            onUserLeft: function(data) {
                removePresenceUser(data);
            }
        });
        
        // Title input handler
        const titleInput = document.getElementById('docTitle');
        if (titleInput) {
            let titleTimeout;
            titleInput.addEventListener('input', function() {
                const newTitle = this.value.trim() || 'Untitled';
                document.title = newTitle + ' - Editor';
                
                clearTimeout(titleTimeout);
                titleTimeout = setTimeout(function() {
                    saveTitle(docId, newTitle);
                }, 1000);
            });
        }
        
        // Word count on load
        updateWordCount(quill, 'wordCount');
        updateLastSaved();
    }
});

// Status badge functions
function setStatus(status, message) {
    const statusBadge = document.getElementById('statusBadge');
    const statusText = document.getElementById('statusText');
    if (!statusBadge || !statusText) return;
    
    statusBadge.className = 'status-badge ' + status;
    statusText.textContent = message;
}

function updateLastSaved() {
    const el = document.getElementById('lastSaved');
    if (!el) return;
    
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    el.textContent = 'Last saved: ' + time;
}

// Presence functions
function addPresenceUser(data) {
    const container = document.getElementById('presenceOthers');
    if (!container) return;
    
    // Check if user already exists
    const existing = document.getElementById('presence-' + data.user_id);
    if (existing) return;
    
    const div = document.createElement('div');
    div.className = 'presence-user';
    div.id = 'presence-' + data.user_id;
    div.innerHTML = \
        <span class="avatar">\</span>
        <span>\</span>
        <span class="status-indicator"></span>
    \;
    container.appendChild(div);
}

function removePresenceUser(data) {
    const el = document.getElementById('presence-' + data.user_id);
    if (el) el.remove();
}
