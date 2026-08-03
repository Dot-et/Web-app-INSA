/* ============================================
   NOTIFICATIONS SYSTEM
   ============================================ */

function showNotification(message, type, duration) {
    const container = document.querySelector('.flash-container');
    if (!container) return;
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + (type || 'success');
    alert.innerHTML = message + ' <button class="close-btn">&times;</button>';
    container.appendChild(alert);
    
    const timeout = duration || 2500;
    setTimeout(function() {
        alert.style.opacity = '0';
        setTimeout(function() { alert.remove(); }, 300);
    }, timeout);
    
    alert.querySelector('.close-btn').addEventListener('click', function() {
        alert.remove();
    });
}

function showToast(message, type) {
    // Simple toast notification
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    const toast = document.createElement('div');
    toast.style.cssText = \
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        background: #1a1a2e;
        color: white;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 9999;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        animation: slideUp 0.3s ease;
        max-width: 350px;
    \;
    
    const icon = icons[type] || 'ℹ️';
    toast.innerHTML = icon + ' ' + message;
    document.body.appendChild(toast);
    
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
}
