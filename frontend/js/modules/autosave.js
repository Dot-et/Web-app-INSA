/* ============================================
   AUTO-SAVE MODULE
   ============================================ */

class AutoSave {
    constructor(options) {
        this.docId = options.docId;
        this.editor = options.editor;
        this.delay = options.delay || 800;
        this.timeout = null;
        this.isSaving = false;
        this.onSaveStart = options.onSaveStart || (() => {});
        this.onSaveEnd = options.onSaveEnd || (() => {});
        this.onError = options.onError || (() => {});
        
        this.init();
    }
    
    init() {
        if (this.editor) {
            this.editor.on('text-change', (delta, oldDelta, source) => {
                if (source === 'user') {
                    this.scheduleSave();
                }
            });
        }
    }
    
    scheduleSave() {
        this.onSaveStart();
        clearTimeout(this.timeout);
        this.timeout = setTimeout(() => {
            this.save();
        }, this.delay);
    }
    
    save() {
        if (this.isSaving) return;
        this.isSaving = true;
        
        const content = this.editor.getContent();
        const url = /api/documents//save;
        
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        })
        .then(response => response.json())
        .then(data => {
            this.isSaving = false;
            if (data.status === 'saved') {
                this.onSaveEnd();
            }
        })
        .catch(() => {
            this.isSaving = false;
            this.onError();
        });
    }
    
    forceSave() {
        this.save();
    }
}
