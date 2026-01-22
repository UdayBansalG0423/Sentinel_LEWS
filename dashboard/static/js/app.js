/**
 * Sentinel-LEWS Dashboard JavaScript
 * Minimal vanilla JS for dashboard functionality
 */

// ===== Global State =====
let systemData = {
    networkStatus: 'OFFLINE',
    lastUpdate: null
};

// ===== Initialize on DOM Load =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    startSystemClock();
    loadSystemSummary();
    setupEventDelegation();
    applyDataWidths();
    
    // Poll for updates every 15 seconds
    setInterval(loadSystemSummary, 15000);
});

// ===== App Initialization =====
function initializeApp() {
    console.log('Sentinel-LEWS Dashboard initialized');
    
    // Check network status
    checkNetworkStatus();
}

// ===== Apply Data Widths =====
function applyDataWidths() {
    // Apply width from data-width attributes to elements
    document.querySelectorAll('[data-width]').forEach(element => {
        const width = element.getAttribute('data-width');
        if (width) {
            element.style.width = width + '%';
        }
    });
}

// ===== Event Delegation for Alert Actions =====
function setupEventDelegation() {
    // Handle all button clicks with data-action attributes
    document.addEventListener('click', function(e) {
        const button = e.target.closest('[data-action]');
        if (!button) return;
        
        const action = button.getAttribute('data-action');
        const alertId = button.getAttribute('data-alert-id');
        
        if (!alertId) return;
        
        switch(action) {
            case 'view':
                viewAlertDetails(alertId);
                break;
            case 'acknowledge':
                acknowledgeAlert(alertId);
                break;
            case 'sms':
                sendSMS(alertId);
                break;
            case 'map':
                viewOnMap(alertId);
                break;
        }
    });
}

// ===== System Clock =====
function startSystemClock() {
    const clockElement = document.getElementById('system-time');
    if (!clockElement) return;
    
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour12: false });
        clockElement.textContent = timeString;
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

// ===== Load System Summary =====
function loadSystemSummary() {
    fetch('/api/summary')
        .then(response => response.json())
        .then(data => {
            systemData = data;
            updateTopBar(data);
            updateOfflineBanner(data.network_status);
        })
        .catch(error => {
            console.error('Failed to load system summary:', error);
            updateOfflineBanner('OFFLINE');
        });
}

// ===== Update Top Bar =====
function updateTopBar(data) {
    // Update network status
    const networkStatus = document.getElementById('network-status');
    if (networkStatus) {
        const statusValue = networkStatus.querySelector('.value');
        if (statusValue) {
            statusValue.textContent = data.network_status || 'OFFLINE';
            statusValue.className = data.network_status === 'ONLINE' ? 'value status-online' : 'value status-offline';
        }
    }
    
    // Update last ingestion
    const lastIngestion = document.getElementById('last-ingestion');
    if (lastIngestion && data.last_ingestion) {
        lastIngestion.textContent = formatTime(data.last_ingestion);
    }
    
    // Update inference latency
    const inferenceLatency = document.getElementById('inference-latency');
    if (inferenceLatency && data.inference_latency) {
        inferenceLatency.textContent = data.inference_latency + ' s';
    }
    
    // Update model version
    const modelVersion = document.getElementById('model-version');
    if (modelVersion && data.model_version) {
        modelVersion.textContent = data.model_version;
    }
}

// ===== Update Offline Banner =====
function updateOfflineBanner(status) {
    const banner = document.getElementById('offline-banner');
    if (!banner) return;
    
    if (status === 'OFFLINE') {
        banner.style.display = 'block';
    } else {
        banner.style.display = 'none';
    }
}

// ===== Check Network Status =====
function checkNetworkStatus() {
    if (!navigator.onLine) {
        updateOfflineBanner('OFFLINE');
    }
    
    window.addEventListener('online', () => {
        console.log('Network: ONLINE');
        loadSystemSummary();
    });
    
    window.addEventListener('offline', () => {
        console.log('Network: OFFLINE');
        updateOfflineBanner('OFFLINE');
    });
}

// ===== Alert Actions =====
function acknowledgeAlert(alertId) {
    if (!confirm('Acknowledge this alert?')) return;
    
    fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Alert acknowledged successfully', 'success');
            // Reload page or update UI
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Failed to acknowledge alert', 'error');
        }
    })
    .catch(error => {
        console.error('Error acknowledging alert:', error);
        showNotification('Error acknowledging alert', 'error');
    });
}

function sendSMS(alertId) {
    if (!confirm('Send SMS alert now?')) return;
    
    fetch(`/api/alerts/${alertId}/send_sms`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('SMS alert sent successfully', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification('Failed to send SMS', 'error');
        }
    })
    .catch(error => {
        console.error('Error sending SMS:', error);
        showNotification('Error sending SMS', 'error');
    });
}

function viewOnMap(alertId) {
    console.log('Viewing alert', alertId, 'on map');
    showNotification('Map view feature in development', 'info');
}

// ===== Utility Functions =====
function timeAgo(timestamp) {
    if (!timestamp) return 'N/A';
    
    const now = new Date();
    const past = new Date(timestamp);
    const diffMs = now - past;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    return `${diffDay}d ago`;
}

function formatTime(timestamp) {
    if (!timestamp) return '--:--';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateTime(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// ===== Notifications =====
function showNotification(message, type = 'info') {
    // Simple alert for now - can be enhanced with toast notifications
    const icons = {
        success: '✓',
        error: '✗',
        info: 'ℹ'
    };
    
    alert(`${icons[type] || 'ℹ'} ${message}`);
}

// ===== Search Functionality =====
const globalSearch = document.getElementById('global-search');
if (globalSearch) {
    globalSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (query) {
                console.log('Search query:', query);
                showNotification('Search feature in development', 'info');
            }
        }
    });
}

// ===== Drawer Functions (for Alerts page) =====
function closeDrawer() {
    const drawer = document.getElementById('alert-details-drawer');
    if (drawer) {
        drawer.classList.remove('active');
    }
}

// Close drawer on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDrawer();
    }
});

// ===== Export Functions =====
function exportData(format = 'json') {
    console.log('Exporting data as', format);
    showNotification(`Exporting data as ${format.toUpperCase()}...`, 'info');
}

// ===== Console =====
console.log('%c Sentinel-LEWS Dashboard ', 'background: #2563eb; color: white; font-size: 14px; padding: 4px 8px;');
console.log('District-level landslide early warning system');
console.log('Offline-capable emergency control panel');
