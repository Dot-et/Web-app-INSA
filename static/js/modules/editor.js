/* ============================================
   EDITOR CORE MODULE
   ============================================ */

class Editor {
    constructor(options) {
        this.docId = options.docId;
        this.userId = options.userId;
        this.username = options.username;
        this.container = options.container || '#editor-container';
        this.placeholder = options.placeholder || 'Start writing your document...';
        this.quill = null;
        
        this.init();
    }
    
    init() {
        this.quill = new Quill(this.container, {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'color': [] }, { 'background': [] }],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }, { 'list': 'check' }],
                    [{ 'indent': '-1'}, { 'indent': '+1' }],
                    [{ 'align': [] }],
                    ['link', 'image'],
                    ['blockquote', 'code-block'],
                    ['clean']
                ]
            },
            placeholder: this.placeholder
        });
    }
    
    getContent() {
        return this.quill ? this.quill.root.innerHTML : '';
    }
    
    setContent(content) {
        if (this.quill) {
            this.quill.root.innerHTML = content;
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
    
    destroy() {
        if (this.quill) {
            this.quill = null;
        }
    }
}
