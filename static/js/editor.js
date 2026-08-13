/**
 * EDITOR MODULE
 * Handles the rich text editor
 */

class Editor {
    constructor(options) {
        this.docId = options.docId;
        this.userId = options.userId;
        this.username = options.username;
        this.container = options.container || '#editor';
        this.placeholder = options.placeholder || 'Start writing your document...';
        this.quill = null;
        this.initialContentSet = false;
        this.init();
    }
    
    init() {
        // Check if Quill is available
        if (typeof Quill === 'undefined') {
            console.error('Quill library not loaded');
            return;
        }
        
        // Check if container exists
        const containerEl = document.querySelector(this.container);
        if (!containerEl) {
            console.error('Editor container not found:', this.container);
            return;
        }
        
        this.quill = new Quill(this.container, {
            theme: 'snow',
            modules: {
                toolbar: '#toolbar',
                history: {
                    delay: 1000,
                    maxStack: 100,
                    userOnly: true
                }
            },
            placeholder: this.placeholder
        });
        
        console.log('✅ Editor initialized');
    }
    
    getContent() {
        return this.quill ? this.quill.root.innerHTML : '';
    }
    
    setContent(content) {
        if (this.quill && content !== undefined) {
            const current = this.quill.root.innerHTML;
            if (content !== current) {
                console.log('📝 Setting editor content, length:', content.length);
                this.quill.root.innerHTML = content;
                this.initialContentSet = true;
            }
        }
    }
    
    getText() {
        return this.quill ? this.quill.getText() : '';
    }
    
    getWordCount() {
        const text = this.getText().trim();
        return text ? text.split(/\s+/).length : 0;
    }
    
    on(event, callback) {
        if (this.quill) {
            this.quill.on(event, callback);
        }
    }
    
    off(event, callback) {
        if (this.quill) {
            this.quill.off(event, callback);
        }
    }
    
    getSelection() {
        return this.quill ? this.quill.getSelection() : null;
    }
    
    setSelection(index, length) {
        if (this.quill) {
            this.quill.setSelection(index, length);
        }
    }
    
    format(name, value) {
        if (this.quill) {
            this.quill.format(name, value);
        }
    }
    
    destroy() {
        if (this.quill) {
            this.quill = null;
        }
    }
}