/* ============================================
   MAIN APPLICATION
   ============================================ */

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
        container: '#editor-container'
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
        onError: () => UI.setStatus('', 'Error saving')
    });
    
    // Initialize Real-Time
    const realtime = new RealTime({
        docId: docId,
        editor: editor,
        onUserJoined: (data) => UI.addPresenceUser(data),
        onUserLeft: (data) => UI.removePresenceUser(data),
        onUpdate: (data) => {
            UI.updateWordCount(editor.getWordCount());
            UI.updateLastSaved();
            UI.showNotification('✏️ Updated by ' + data.user);
        }
    });
    
    // Update word count on changes
    editor.on('text-change', () => {
        UI.updateWordCount(editor.getWordCount());
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
            document.title = newTitle + ' - Editor';
            
            clearTimeout(titleTimeout);
            titleTimeout = setTimeout(() => {
                fetch('/api/documents/' + docId + '/rename', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: newTitle })
                });
            }, 1000);
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            autosave.forceSave();
            UI.showNotification('Document saved! ✅');
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        realtime.leaveDocument();
    });
});
