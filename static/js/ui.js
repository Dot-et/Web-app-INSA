/**
 * UI HELPER MODULE
 * Handles UI updates and notifications
 */

class UI {
    static setStatus(status, message) {
        const dot = document.getElementById('statusDot');
        const text = document.getElementById('statusText');
        if (dot && text) {
            dot.className = 'dot ' + status;
            text.innerText = message;
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
                minute: '2-digit',
                second: '2-digit'
            });
            el.innerHTML = '<i class="fas fa-save"></i> Last saved: ' + time;
        }
    }
    
    static showNotification(message, type = 'info') {
        // Use toast for non-error messages
        if (type !== 'danger' && type !== 'error') {
            this.showToast(message, type);
            return;
        }
        
        // Use flash for errors
        const container = document.querySelector('.flash-container');
        if (!container) return;
        
        const alert = document.createElement('div');
        alert.className = 'alert alert-' + type;
        alert.innerHTML = message + ' <button class="close-btn">&times;</button>';
        container.appendChild(alert);
        
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() { alert.remove(); }, 300);
        }, 4000);
        
        alert.querySelector('.close-btn').addEventListener('click', function() {
            alert.remove();
        });
    }
    
    static showToast(message, type = 'info') {
        // Remove existing toast
        const existing = document.querySelector('.toast-notification');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        
        // Set colors based on type
        const colors = {
            success: { bg: '#2ecc71', icon: 'fa-check-circle' },
            error: { bg: '#e74c3c', icon: 'fa-exclamation-circle' },
            warning: { bg: '#f39c12', icon: 'fa-exclamation-triangle' },
            info: { bg: '#4a90d9', icon: 'fa-info-circle' }
        };
        const color = colors[type] || colors.info;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${color.bg};
            color: white;
            padding: 14px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            z-index: 99999;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            animation: slideInRight 0.4s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 400px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
        `;
        
        toast.innerHTML = `
            <i class="fas ${color.icon}" style="font-size: 18px;"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" style="
                background: none; 
                border: none; 
                color: rgba(255,255,255,0.7); 
                cursor: pointer; 
                font-size: 16px;
                padding: 0 4px;
            ">&times;</button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 3.5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideOutRight 0.4s ease';
                setTimeout(() => toast.remove(), 400);
            }
        }, 3500);
    }
    
    static addPresenceUser(data) {
        const container = document.getElementById('presence-others');
        if (!container) return;
        
        const existing = document.getElementById('presence-' + data.user_id);
        if (existing) return;
        
        const div = document.createElement('div');
        div.className = 'presence-user';
        div.id = 'presence-' + data.user_id;
        div.innerHTML = `
            <span class="avatar">${data.username[0].toUpperCase()}</span>
            <span>${data.username}</span>
            <span class="status-indicator"></span>
        `;
        container.appendChild(div);
    }
    
    static removePresenceUser(data) {
        const el = document.getElementById('presence-' + data.user_id);
        if (el) el.remove();
    }
}

// Add CSS animations for toasts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(100px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideOutRight {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100px); }
    }
`;
document.head.appendChild(style);