/* ============================================
   KEYBOARD SHORTCUTS
   ============================================ */

function initShortcuts(handlers) {
    document.addEventListener('keydown', function(e) {
        // Ctrl + S - Save
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            if (handlers.save) handlers.save();
        }
        
        // Ctrl + B - Bold
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            if (handlers.bold) handlers.bold();
        }
        
        // Ctrl + I - Italic
        if (e.ctrlKey && e.key === 'i') {
            e.preventDefault();
            if (handlers.italic) handlers.italic();
        }
        
        // Ctrl + U - Underline
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            if (handlers.underline) handlers.underline();
        }
        
        // Ctrl + Z - Undo
        if (e.ctrlKey && e.key === 'z') {
            e.preventDefault();
            if (handlers.undo) handlers.undo();
        }
        
        // Ctrl + Y - Redo
        if (e.ctrlKey && e.key === 'y') {
            e.preventDefault();
            if (handlers.redo) handlers.redo();
        }
        
        // Ctrl + Shift + V - Versions
        if (e.ctrlKey && e.shiftKey && e.key === 'v') {
            e.preventDefault();
            if (handlers.versions) handlers.versions();
        }
    });
}

function shortcutHelp() {
    return [
        { keys: 'Ctrl+S', description: 'Save document' },
        { keys: 'Ctrl+B', description: 'Bold text' },
        { keys: 'Ctrl+I', description: 'Italic text' },
        { keys: 'Ctrl+U', description: 'Underline text' },
        { keys: 'Ctrl+Z', description: 'Undo' },
        { keys: 'Ctrl+Y', description: 'Redo' },
        { keys: 'Ctrl+Shift+V', description: 'View versions' }
    ];
}
