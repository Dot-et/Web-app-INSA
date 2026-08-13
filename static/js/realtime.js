/**
 * REAL-TIME MODULE
 * Handles Socket.IO real-time collaboration with cursor tracking
 */

class RealTime {
    constructor(options) {
        this.docId = options.docId;
        this.editor = options.editor;
        this.onUserJoined = options.onUserJoined || (() => {});
        this.onUserLeft = options.onUserLeft || (() => {});
        this.onUpdate = options.onUpdate || (() => {});
        this.onTyping = options.onTyping || (() => {});
        this.onStopTyping = options.onStopTyping || (() => {});
        this.socket = null;
        this.users = {};
        this.isUpdating = false;
        this.cursors = {};
        this.typingTimers = {};
        this.init();
    }
    
    init() {
        console.log('🔄 Initializing RealTime');
        
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded');
            return;
        }
        
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('✅ Connected to real-time server');
            this.joinDocument();
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from real-time server');
        });
        
        this.socket.on('connect_error', (error) => {
            console.log('❌ Connection error:', error);
        });
        
        // Document updates
        this.socket.on('document_updated', (data) => {
            console.log('📝 Document updated by:', data.user);
            
            if (this.editor) {
                const currentContent = this.editor.getContent();
                if (data.content !== currentContent) {
                    console.log('🔄 Updating editor content');
                    this.isUpdating = true;
                    this.editor.setContent(data.content);
                    this.onUpdate(data);
                    setTimeout(() => {
                        this.isUpdating = false;
                    }, 100);
                }
            }
        });
        
        // User joined
        this.socket.on('user_joined', (data) => {
            console.log('👤 User joined:', data.username);
            this.users[data.user_id] = data.username;
            this.onUserJoined(data);
        });
        
        // User left
        this.socket.on('user_left', (data) => {
            console.log('👤 User left:', data.username);
            delete this.users[data.user_id];
            this.removeCursor(data.user_id);
            this.onUserLeft(data);
        });
        
        // Cursor updates
        this.socket.on('cursor_update', (data) => {
            console.log('🖱️ Cursor update from:', data.user);
            this.updateCursor(data);
        });
        
        // Typing indicators
        this.socket.on('user_typing', (data) => {
            console.log('⌨️ User typing:', data.username);
            this.onTyping(data);
            
            // Clear existing timer
            if (this.typingTimers[data.user_id]) {
                clearTimeout(this.typingTimers[data.user_id]);
            }
            
            // Auto-stop after 3 seconds of no typing
            this.typingTimers[data.user_id] = setTimeout(() => {
                this.onStopTyping({ user_id: data.user_id, username: data.username });
                delete this.typingTimers[data.user_id];
            }, 3000);
        });
        
        this.socket.on('user_stop_typing', (data) => {
            console.log('⌨️ User stopped typing:', data.username);
            this.onStopTyping(data);
            if (this.typingTimers[data.user_id]) {
                clearTimeout(this.typingTimers[data.user_id]);
                delete this.typingTimers[data.user_id];
            }
        });
    }
    
    joinDocument() {
        if (this.socket && this.docId) {
            console.log('📄 Joining document:', this.docId);
            this.socket.emit('join_document', { doc_id: this.docId });
        }
    }
    
    leaveDocument() {
        if (this.socket && this.docId) {
            console.log('📄 Leaving document:', this.docId);
            this.socket.emit('leave_document', { doc_id: this.docId });
        }
    }
    
    sendChange(content) {
        if (this.socket && this.docId && !this.isUpdating) {
            this.socket.emit('document_change', {
                doc_id: this.docId,
                content: content
            });
        }
    }
    
    sendCursor(index) {
        if (this.socket && this.docId) {
            this.socket.emit('cursor_move', {
                doc_id: this.docId,
                index: index
            });
        }
    }
    
    sendTyping() {
        if (this.socket && this.docId) {
            this.socket.emit('typing', { doc_id: this.docId });
        }
    }
    
    sendStopTyping() {
        if (this.socket && this.docId) {
            this.socket.emit('stop_typing', { doc_id: this.docId });
        }
    }
    
    updateCursor(data) {
        // Remove old cursor
        this.removeCursor(data.user_id);
        
        // Get the editor element
        const editorEl = document.getElementById('editor');
        if (!editorEl) return;
        
        // Create cursor element
        const cursor = document.createElement('div');
        cursor.className = 'remote-cursor';
        cursor.id = 'cursor-' + data.user_id;
        cursor.style.background = this.getColor(data.user_id);
        
        // Create label
        const label = document.createElement('span');
        label.className = 'remote-cursor-label';
        label.textContent = data.username || 'User';
        label.style.background = this.getColor(data.user_id);
        cursor.appendChild(label);
        
        // Position the cursor
        // This is simplified - in production you'd use a more accurate positioning
        const range = this.getTextRange(data.index || 0);
        if (range) {
            const rect = range.getBoundingClientRect();
            const editorRect = editorEl.getBoundingClientRect();
            cursor.style.left = (rect.left - editorRect.left) + 'px';
            cursor.style.top = (rect.top - editorRect.top) + 'px';
        }
        
        editorEl.style.position = 'relative';
        editorEl.appendChild(cursor);
        
        this.cursors[data.user_id] = cursor;
    }
    
    removeCursor(userId) {
        if (this.cursors[userId]) {
            this.cursors[userId].remove();
            delete this.cursors[userId];
        }
    }
    
    getTextRange(index) {
        const editorEl = document.getElementById('editor');
        if (!editorEl) return null;
        
        const range = document.createRange();
        const textNode = editorEl.firstChild;
        if (textNode && textNode.textContent.length >= index) {
            range.setStart(textNode, Math.min(index, textNode.textContent.length));
            range.collapse(true);
            return range;
        }
        return null;
    }
    
    getColor(userId) {
        const colors = ['#4a90d9', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c'];
        return colors[userId % colors.length];
    }
    
    getUsers() {
        return this.users;
    }
}