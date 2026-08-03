/* ============================================
   AUTO-SAVE SYSTEM
   ============================================ */

let saveTimeout = null;
let isSaving = false;

function initAutoSave(quill, docId, options) {
    const {
        onSaveStart = () => {},
        onSaveEnd = () => {},
        onError = () => {},
        delay = 800
    } = options || {};
    
    quill.on('text-change', function(delta, oldDelta, source) {
        if (source === 'user') {
            const content = quill.root.innerHTML;
            onSaveStart();
            
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(function() {
                saveDocument(docId, content, onSaveEnd, onError);
            }, delay);
        }
    });
}

function saveDocument(docId, content, onSuccess, onError) {
    if (isSaving) return;
    isSaving = true;
    
    fetch('/api/documents/' + docId + '/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        isSaving = false;
        if (data.status === 'saved' && onSuccess) {
            onSuccess();
        }
    })
    .catch(() => {
        isSaving = false;
        if (onError) onError();
    });
}

function saveTitle(docId, title, onSuccess, onError) {
    fetch('/api/documents/' + docId + '/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'renamed' && onSuccess) {
            onSuccess();
        }
    })
    .catch(() => {
        if (onError) onError();
    });
}
