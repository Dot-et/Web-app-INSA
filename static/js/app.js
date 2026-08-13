/**
 * MAIN APPLICATION
 * Initializes the collaborative document editor with all features
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('editor-container');
    if (!container) return;
    
    // Get data from container
    const docId = parseInt(container.dataset.docId);
    const userId = parseInt(container.dataset.userId);
    const username = container.dataset.username;
    const initialContent = container.dataset.content || '';
    
    // Initialize Editor
    const editor = new Editor({
        docId: docId,
        userId: userId,
        username: username,
        container: '#editor'
    });
    editor.setContent(initialContent);
    
    // Initialize Auto-Save
    const autosave = new AutoSave({
        docId: docId,
        editor: editor,
        onSaveStart: () => UI.setStatus('saving', 'Saving...'),
        onSaveEnd: () => {
            UI.setStatus('', 'Saved');
            UI.updateLastSaved();
        },
        onError: () => UI.setStatus('error', 'Error saving')
    });
    
    // Initialize Real-Time with typing indicators
    const realtime = new RealTime({
        docId: docId,
        editor: editor,
        onUserJoined: (data) => {
            UI.addPresenceUser(data);
            UI.showNotification('👤 ' + data.username + ' joined the document', 'info');
        },
        onUserLeft: (data) => {
            UI.removePresenceUser(data);
            UI.showNotification('👤 ' + data.username + ' left the document', 'info');
        },
        onUpdate: (data) => {
            UI.updateWordCount(editor.getWordCount());
            UI.updateLastSaved();
            if (data.user && data.user !== username) {
                UI.showNotification('✏️ ' + data.user + ' updated the document', 'info');
            }
        },
        onTyping: (data) => {
            showTypingIndicator(data.username + ' is typing...');
        },
        onStopTyping: (data) => {
            hideTypingIndicator(data.username);
        }
    });
    
    // Update word count on changes
    editor.on('text-change', function(delta, oldDelta, source) {
        if (source === 'user') {
            const content = editor.getContent();
            
            // Update UI
            UI.updateWordCount(editor.getWordCount());
            
            // Send to other users
            realtime.sendChange(content);
            
            // Send typing indicator
            realtime.sendTyping();
            
            // Auto-stop typing after 1 second
            clearTimeout(window.typingTimeout);
            window.typingTimeout = setTimeout(() => {
                realtime.sendStopTyping();
            }, 1000);
        }
    });
    
    // Track cursor position
    editor.on('selection-change', function(range, oldRange, source) {
        if (source === 'user' && range) {
            const index = range.index || 0;
            realtime.sendCursor(index);
        }
    });
    
    // Initial word count
    UI.updateWordCount(editor.getWordCount());
    UI.updateLastSaved();
    
    // Title auto-save
    const titleInput = document.getElementById('docTitle');
    let titleTimeout;
    
    if (titleInput) {
        titleInput.addEventListener('input', function() {
            const newTitle = this.value.trim() || 'Untitled';
            document.title = newTitle + ' - Collaborative Editor';
            
            clearTimeout(titleTimeout);
            titleTimeout = setTimeout(() => {
                fetch('/documents/' + docId + '/api/rename', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: newTitle })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'renamed') {
                        UI.showNotification('Document renamed!', 'success');
                    }
                })
                .catch(() => {
                    UI.showNotification('Failed to rename', 'danger');
                });
            }, 1000);
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            autosave.forceSave();
            UI.showNotification('Document saved! ✅', 'success');
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        realtime.leaveDocument();
    });
});

// ============================================
// TYPING INDICATOR UI
// ============================================

function showTypingIndicator(message) {
    const el = document.getElementById('typing-indicators');
    if (el) {
        el.textContent = '⌨️ ' + message;
        el.style.display = 'block';
    }
}

function hideTypingIndicator(username) {
    const el = document.getElementById('typing-indicators');
    if (el && el.textContent.includes(username)) {
        el.textContent = '';
        el.style.display = 'none';
    }
}