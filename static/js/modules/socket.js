/* ============================================
   SOCKET.IO REAL-TIME MODULE
   ============================================ */

class RealTime {
    constructor(options) {
        this.docId = options.docId;
        this.editor = options.editor;
        this.onUserJoined = options.onUserJoined || (() => {});
        this.onUserLeft = options.onUserLeft || (() => {});
        this.onUpdate = options.onUpdate || (() => {});
        this.socket = null;
        this.users = {};
        
        this.init();
    }
    
    init() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to real-time server');
            this.joinDocument();
        });
        
        this.socket.on('document_updated', (data) => {
            if (this.editor) {
                const current = this.editor.getContent();
                if (data.content !== current) {
                    this.editor.setContent(data.content);
                    this.onUpdate(data);
                }
            }
        });
        
        this.socket.on('user_joined', (data) => {
            this.users[data.user_id] = data.username;
            this.onUserJoined(data);
        });
        
        this.socket.on('user_left', (data) => {
            delete this.users[data.user_id];
            this.onUserLeft(data);
        });
    }
    
    joinDocument() {
        if (this.socket && this.docId) {
            this.socket.emit('join_document', { doc_id: this.docId });
        }
    }
    
    leaveDocument() {
        if (this.socket && this.docId) {
            this.socket.emit('leave_document', { doc_id: this.docId });
        }
    }
    
    sendChange(content) {
        if (this.socket && this.docId) {
            this.socket.emit('document_change', {
                doc_id: this.docId,
                content: content
            });
        }
    }
    
    getUsers() {
        return this.users;
    }
}
