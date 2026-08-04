/* ============================================
   UI HELPER MODULE
   ============================================ */

class UI {
    static setStatus(status, message) {
        const badge = document.getElementById('statusBadge');
        const text = document.getElementById('statusText');
        if (badge && text) {
            badge.className = 'status-badge ' + status;
            text.textContent = message;
        }
    }
    
    static updateWordCount(count) {
        const el = document.getElementById('wordCount');
        if (el) el.textContent = count;
    }
    
    static updateLastSaved() {
        const el = document.getElementById('lastSaved');
        if (el) {
            const now = new Date();
            const time = now.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            el.textContent = 'Last saved: ' + time;
        }
    }
    
    static showNotification(message, type = 'success') {
        const container = document.querySelector('.flash-container');
        if (!container) return;
        
        const alert = document.createElement('div');
        alert.className = 'alert alert-' + type;
        alert.innerHTML = message + ' <button class="close-btn">&times;</button>';
        container.appendChild(alert);
        
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 2500);
        
        alert.querySelector('.close-btn').addEventListener('click', () => alert.remove());
    }
    
    static addPresenceUser(data) {
        const container = document.getElementById('presence-others');
        if (!container) return;
        
        const existing = document.getElementById('presence-' + data.user_id);
        if (existing) return;
        
        const div = document.createElement('div');
        div.className = 'presence-user';
        div.id = 'presence-' + data.user_id;
        div.innerHTML = \
            <span class="avatar">\</span>
            <span>\</span>
            <span class="status-indicator"></span>
        \;
        container.appendChild(div);
    }
    
    static removePresenceUser(data) {
        const el = document.getElementById('presence-' + data.user_id);
        if (el) el.remove();
    }
}
