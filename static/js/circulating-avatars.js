/**
 * SKAILA - Circulating Avatars Component
 * Displays online users as avatars circulating around messaging button
 * Real-time updates via Socket.IO
 */

class CirculatingAvatars {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }
        
        this.options = {
            maxAvatars: 7,
            orbitRadius: 50, // pixels
            avatarSize: 28,  // pixels
            animationDuration: 15, // seconds (full rotation)
            updateInterval: 30000, // 30 seconds
            ...options
        };
        
        this.onlineUsers = [];
        this.socket = null;
        this.updateTimer = null;
        
        this.init();
    }
    
    init() {
        // Add container class for styling
        this.container.classList.add('circulating-avatars-container');
        
        // Fetch initial online users
        this.fetchOnlineUsers();
        
        // Setup Socket.IO listeners for real-time updates
        this.setupSocketListeners();
        
        // Periodic refresh
        this.startPeriodicUpdates();
    }
    
    async fetchOnlineUsers() {
        try {
            const response = await fetch('/api/online-users');
            if (!response.ok) {
                throw new Error('Failed to fetch online users');
            }
            
            const data = await response.json();
            this.onlineUsers = data.users || [];
            this.renderAvatars();
        } catch (error) {
            console.error('Error fetching online users:', error);
        }
    }
    
    setupSocketListeners() {
        // Connect to Socket.IO (assumes global socket connection exists)
        if (typeof io !== 'undefined' && window.socket) {
            this.socket = window.socket;
            
            // Listen for user connected events
            this.socket.on('user_connected', (data) => {
                console.log('👤 User connected:', data);
                this.fetchOnlineUsers(); // Refresh list
            });
            
            // Listen for user disconnected events
            this.socket.on('user_disconnected', (data) => {
                console.log('👤 User disconnected:', data);
                this.fetchOnlineUsers(); // Refresh list
            });
        }
    }
    
    startPeriodicUpdates() {
        // Refresh every 30 seconds as fallback
        this.updateTimer = setInterval(() => {
            this.fetchOnlineUsers();
        }, this.options.updateInterval);
    }
    
    renderAvatars() {
        // Clear existing avatars
        const existingAvatars = this.container.querySelectorAll('.orbit-avatar');
        existingAvatars.forEach(avatar => avatar.remove());
        
        // Limit to maxAvatars
        const usersToDisplay = this.onlineUsers.slice(0, this.options.maxAvatars);
        
        if (usersToDisplay.length === 0) {
            return; // No online users to display
        }
        
        // Calculate even spacing around circle
        const angleStep = 360 / usersToDisplay.length;
        
        usersToDisplay.forEach((user, index) => {
            const avatar = this.createAvatarElement(user, index, angleStep);
            this.container.appendChild(avatar);
        });
    }
    
    createAvatarElement(user, index, angleStep) {
        const avatar = document.createElement('div');
        avatar.className = 'orbit-avatar';
        avatar.dataset.userId = user.id;
        avatar.dataset.userName = user.name;
        
        // Calculate position on orbit
        const startAngle = index * angleStep;
        
        // Set CSS custom properties for animation
        avatar.style.setProperty('--orbit-radius', `${this.options.orbitRadius}px`);
        avatar.style.setProperty('--avatar-size', `${this.options.avatarSize}px`);
        avatar.style.setProperty('--start-angle', `${startAngle}deg`);
        avatar.style.setProperty('--animation-duration', `${this.options.animationDuration}s`);
        avatar.style.setProperty('--animation-delay', `${-index * 0.3}s`); // Stagger effect
        
        // Create avatar content
        const avatarInner = document.createElement('div');
        avatarInner.className = 'orbit-avatar-inner';
        avatarInner.style.backgroundColor = user.avatar_color || '#003B73';
        avatarInner.textContent = user.initials || '??';
        
        // Tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'orbit-avatar-tooltip';
        tooltip.textContent = user.name;
        
        avatar.appendChild(avatarInner);
        avatar.appendChild(tooltip);
        
        return avatar;
    }
    
    destroy() {
        // Cleanup
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        if (this.socket) {
            this.socket.off('user_connected');
            this.socket.off('user_disconnected');
        }
        
        const existingAvatars = this.container.querySelectorAll('.orbit-avatar');
        existingAvatars.forEach(avatar => avatar.remove());
    }
}

// Make available globally
window.CirculatingAvatars = CirculatingAvatars;
