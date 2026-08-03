/* ============================================
   EDITOR CORE
   ============================================ */

let quill = null;
let docId = null;
let userId = null;
let username = '';

function initEditor(elementId, options) {
    docId = options.docId;
    userId = options.userId;
    username = options.username;
    
    quill = new Quill(elementId, {
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
        placeholder: options.placeholder || 'Start writing your document...'
    });
    
    // Set initial content
    if (options.content) {
        quill.root.innerHTML = options.content;
    }
    
    return quill;
}

function getEditorContent() {
    return quill ? quill.root.innerHTML : '';
}

function setEditorContent(content) {
    if (quill) {
        quill.root.innerHTML = content;
    }
}

function getEditorText() {
    return quill ? quill.getText() : '';
}
