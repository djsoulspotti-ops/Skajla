/**
 * SKAILA Network Manager
 * Gestione avanzata connessione Socket.IO con heartbeat, presence e notifiche
 */

class SKAILANetworkManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.heartbeatInterval = null;
        this.presenceInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.heartbeatRate = 30000;
        this.presenceRate = 60000;
        this.onlineUsers = new Set();
        this.eventHandlers = {};
    }

    init(socketInstance) {
        this.socket = socketInstance;
        this.setupConnectionHandlers();
        this.setupPresenceHandlers();
        this.setupNotificationHandlers();
        this.setupMessageHandlers();
        console.log('🌐 SKAILA Network Manager initialized');
    }

    setupConnectionHandlers() {
        this.socket.on('connect', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            this.startPresencePing();
            this.requestOnlineUsers();
            console.log('✅ Connected to SKAILA Network');
            this.emit('network:connected');
        });

        this.socket.on('disconnect', () => {
            this.connected = false;
            this.stopHeartbeat();
            this.stopPresencePing();
            console.log('❌ Disconnected from SKAILA Network');
            this.emit('network:disconnected');
        });

        this.socket.on('connect_error', (error) => {
            console.warn('⚠️ Connection error:', error.message);
            this.reconnectAttempts++;
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.emit('network:failed');
            }
        });

        this.socket.on('heartbeat_ack', (data) => {
            this.emit('heartbeat:ack', data);
        });

        this.socket.on('pong_presence', (data) => {
            this.emit('presence:pong', data);
        });
    }

    setupPresenceHandlers() {
        this.socket.on('user_connected', (data) => {
            this.onlineUsers.add(data.user_id);
            this.emit('presence:user_online', data);
            this.updatePresenceUI(data.user_id, true);
        });

        this.socket.on('user_disconnected', (data) => {
            this.onlineUsers.delete(data.user_id);
            this.emit('presence:user_offline', data);
            this.updatePresenceUI(data.user_id, false);
        });

        this.socket.on('online_users_list', (data) => {
            this.onlineUsers = new Set(data.users || []);
            this.emit('presence:list_updated', data);
            this.updateAllPresenceUI();
        });

        this.socket.on('room_presence', (data) => {
            this.emit('presence:room', data);
        });
    }

    setupNotificationHandlers() {
        this.socket.on('notification', (data) => {
            this.showNotification(data);
            this.emit('notification:received', data);
        });

        this.socket.on('announcement', (data) => {
            this.showAnnouncement(data);
            this.emit('announcement:received', data);
        });
    }

    setupMessageHandlers() {
        this.socket.on('new_message', (data) => {
            this.emit('message:new', data);
            this.confirmMessageReceived(data.id, data.chat_id);
        });

        this.socket.on('message_delivered', (data) => {
            this.emit('message:delivered', data);
            this.updateMessageStatus(data.message_id, 'delivered');
        });

        this.socket.on('messages_read', (data) => {
            this.emit('message:read', data);
            this.updateMessagesReadStatus(data);
        });

        this.socket.on('user_typing', (data) => {
            this.emit('typing:update', data);
        });

        this.socket.on('error', (data) => {
            console.error('Socket error:', data.message);
            this.emit('error', data);
        });
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            if (this.connected) {
                this.socket.emit('heartbeat');
            }
        }, this.heartbeatRate);
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    startPresencePing() {
        this.stopPresencePing();
        this.presenceInterval = setInterval(() => {
            if (this.connected) {
                this.socket.emit('ping_presence');
            }
        }, this.presenceRate);
    }

    stopPresencePing() {
        if (this.presenceInterval) {
            clearInterval(this.presenceInterval);
            this.presenceInterval = null;
        }
    }

    requestOnlineUsers() {
        if (this.connected) {
            this.socket.emit('request_online_users');
        }
    }

    joinConversation(conversationId) {
        this.socket.emit('join_conversation', { conversation_id: conversationId });
    }

    sendMessage(conversationId, content) {
        this.socket.emit('send_message', {
            conversation_id: conversationId,
            contenuto: content
        });
    }

    markMessagesRead(conversationId, messageIds = null) {
        this.socket.emit('mark_messages_read', {
            conversation_id: conversationId,
            message_ids: messageIds
        });
    }

    confirmMessageReceived(messageId, conversationId) {
        this.socket.emit('confirm_message_received', {
            message_id: messageId,
            conversation_id: conversationId
        });
    }

    startTyping(conversationId) {
        this.socket.emit('typing_start', { conversation_id: conversationId });
    }

    stopTyping(conversationId) {
        this.socket.emit('typing_stop', { conversation_id: conversationId });
    }

    joinClassRoom(classId) {
        this.socket.emit('join_class_room', { class_id: classId });
    }

    leaveClassRoom(classId) {
        this.socket.emit('leave_class_room', { class_id: classId });
    }

    joinSubjectRoom(subjectId) {
        this.socket.emit('join_subject_room', { subject_id: subjectId });
    }

    getRoomPresence(roomType, roomId) {
        this.socket.emit('get_room_presence', { room_type: roomType, room_id: roomId });
    }

    sendNotification(targetType, targetId, title, message, type = 'info') {
        this.socket.emit('send_notification', {
            target_type: targetType,
            target_id: targetId,
            title: title,
            message: message,
            type: type
        });
    }

    broadcastAnnouncement(title, message, priority = 'normal', classId = null) {
        this.socket.emit('broadcast_announcement', {
            title: title,
            message: message,
            priority: priority,
            class_id: classId
        });
    }

    isUserOnline(userId) {
        return this.onlineUsers.has(userId);
    }

    getOnlineUsersCount() {
        return this.onlineUsers.size;
    }

    updatePresenceUI(userId, isOnline) {
        const indicators = document.querySelectorAll(`[data-user-id="${userId}"] .presence-indicator`);
        indicators.forEach(indicator => {
            if (isOnline) {
                indicator.classList.add('online');
                indicator.classList.remove('offline');
            } else {
                indicator.classList.remove('online');
                indicator.classList.add('offline');
            }
        });

        const orbitalIndicators = document.querySelectorAll(`[data-user-id="${userId}"] .orbital-presence`);
        orbitalIndicators.forEach(indicator => {
            if (isOnline) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    updateAllPresenceUI() {
        document.querySelectorAll('[data-user-id]').forEach(el => {
            const userId = parseInt(el.dataset.userId);
            this.updatePresenceUI(userId, this.onlineUsers.has(userId));
        });

        const onlineCounter = document.querySelector('.online-count');
        if (onlineCounter) {
            onlineCounter.textContent = this.onlineUsers.size;
        }
    }

    updateMessageStatus(messageId, status) {
        const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageEl) {
            const statusEl = messageEl.querySelector('.message-status');
            if (statusEl) {
                statusEl.dataset.status = status;
                if (status === 'delivered') {
                    statusEl.innerHTML = '<i class="fas fa-check"></i>';
                } else if (status === 'read') {
                    statusEl.innerHTML = '<i class="fas fa-check-double"></i>';
                }
            }
        }
    }

    updateMessagesReadStatus(data) {
        document.querySelectorAll(`[data-conversation-id="${data.conversation_id}"] .message-own .message-status`).forEach(el => {
            el.dataset.status = 'read';
            el.innerHTML = '<i class="fas fa-check-double text-primary"></i>';
        });
    }

    showNotification(data) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(data.title || 'SKAILA', {
                body: data.message,
                icon: '/static/logo-skaila.svg',
                tag: 'skaila-notification'
            });
        }

        this.showToast(data.type || 'info', data.title, data.message);
    }

    showAnnouncement(data) {
        const priorityClass = data.priority === 'urgent' ? 'announcement-urgent' : 
                             data.priority === 'high' ? 'announcement-high' : 'announcement-normal';

        const announcementHtml = `
            <div class="announcement-banner ${priorityClass}">
                <div class="announcement-icon">
                    <i class="fas fa-bullhorn"></i>
                </div>
                <div class="announcement-content">
                    <strong>${data.title}</strong>
                    <p>${data.message}</p>
                    <small>Da: ${data.sender} (${data.sender_role})</small>
                </div>
                <button class="announcement-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        const container = document.querySelector('.announcements-container') || document.body;
        container.insertAdjacentHTML('afterbegin', announcementHtml);
    }

    showToast(type, title, message) {
        const toastHtml = `
            <div class="toast toast-${type}" role="alert">
                <div class="toast-header">
                    <strong>${title}</strong>
                    <button type="button" class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;

        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            toastContainer.style.cssText = 'position: fixed; top: 1rem; right: 1rem; z-index: 9999;';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);

        const toast = toastContainer.lastElementChild;
        setTimeout(() => toast.remove(), 5000);
    }

    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    off(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
        }
    }

    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => handler(data));
        }
    }

    destroy() {
        this.stopHeartbeat();
        this.stopPresencePing();
        this.eventHandlers = {};
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

window.SKAILANetwork = new SKAILANetworkManager();

document.addEventListener('DOMContentLoaded', function() {
    if (typeof io !== 'undefined' && window.socket) {
        window.SKAILANetwork.init(window.socket);
    }
});
