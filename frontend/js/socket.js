/* ============================================
   SOCKET.IO REAL-TIME
   ============================================ */

let socket = null;
let roomId = null;

function initSocket(options) {
    const { onConnect, onDocumentUpdate, onUserJoined, onUserLeft } = options || {};
    
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        if (onConnect) onConnect();
    });
    
    socket.on('document_updated', function(data) {
        if (onDocumentUpdate) onDocumentUpdate(data);
    });
    
    socket.on('user_joined', function(data) {
        if (onUserJoined) onUserJoined(data);
    });
    
    socket.on('user_left', function(data) {
        if (onUserLeft) onUserLeft(data);
    });
    
    return socket;
}

function joinDocumentRoom(docId) {
    roomId = docId;
    if (socket) {
        socket.emit('join_document', { doc_id: docId });
    }
}

function leaveDocumentRoom() {
    if (socket && roomId) {
        socket.emit('leave_document', { doc_id: roomId });
    }
}

function sendDocumentChange(content) {
    if (socket && roomId) {
        socket.emit('document_change', {
            doc_id: roomId,
            content: content
        });
    }
}
