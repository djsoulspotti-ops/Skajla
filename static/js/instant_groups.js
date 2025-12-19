/**
 * Instant Groups Frontend
 * Gestione UI per gruppi istantanei
 */

class InstantGroupsManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('🚀 Instant Groups Manager initialized');
        this.setupEventListeners();
        this.startCountdownUpdates();
    }

    setupEventListeners() {
        // Pulsante crea gruppo
        const createBtn = document.getElementById('createInstantGroupBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.openCreateModal());
        }

        // Form creazione gruppo
        const createForm = document.getElementById('createInstantGroupForm');
        if (createForm) {
            createForm.addEventListener('submit', (e) => this.handleCreateGroup(e));
        }

        // Toggle pubblico/privato
        const pubblicoCheckbox = document.getElementById('gruppoP ubblico');
        if (pubblicoCheckbox) {
            pubblicoCheckbox.addEventListener('change', (e) => {
                const inviteSection = document.getElementById('inviteUsersSection');
                if (inviteSection) {
                    inviteSection.style.display = e.target.checked ? 'none' : 'block';
                }
            });
        }
    }

    openCreateModal() {
        const modal = document.getElementById('createInstantGroupModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeCreateModal() {
        const modal = document.getElementById('createInstantGroupModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    async handleCreateGroup(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = {
            nome: formData.get('nome'),
            argomento: formData.get('argomento'),
            descrizione: formData.get('descrizione') || '',
            durata_ore: parseInt(formData.get('durata_ore')) || 24,
            pubblico: formData.get('pubblico') === 'on',
            invitati: this.getSelectedUsers()
        };

        try {
            const response = await fetch('/api/chat/instant/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('✅ Gruppo creato con successo!', 'success');
                this.closeCreateModal();
                
                // Ricarica pagina per mostrare nuovo gruppo
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showNotification('❌ ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Errore creazione gruppo:', error);
            this.showNotification('❌ Errore di connessione', 'error');
        }
    }

    async joinGroup(chatId) {
        if (!confirm('Vuoi unirti a questo gruppo?')) return;

        try {
            const response = await fetch(`/api/chat/instant/join/${chatId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('✅ Ti sei unito al gruppo!', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showNotification('❌ ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Errore join gruppo:', error);
            this.showNotification('❌ Errore di connessione', 'error');
        }
    }

    async leaveGroup(chatId) {
        if (!confirm('Vuoi lasciare questo gruppo?')) return;

        try {
            const response = await fetch(`/api/chat/instant/leave/${chatId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('✅ Hai lasciato il gruppo', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showNotification('❌ ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Errore leave gruppo:', error);
            this.showNotification('❌ Errore di connessione', 'error');
        }
    }

    async deleteGroup(chatId) {
        if (!confirm('⚠️ Sei sicuro di voler eliminare questo gruppo? Questa azione è irreversibile!')) return;

        try {
            const response = await fetch(`/api/chat/instant/delete/${chatId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('✅ Gruppo eliminato', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showNotification('❌ ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Errore delete gruppo:', error);
            this.showNotification('❌ Errore di connessione', 'error');
        }
    }

    getSelectedUsers() {
        const checkboxes = document.querySelectorAll('input[name="invitati"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value));
    }

    startCountdownUpdates() {
        // Aggiorna countdown ogni minuto
        setInterval(() => this.updateCountdowns(), 60000);
        this.updateCountdowns(); // Prima esecuzione immediata
    }

    updateCountdowns() {
        const countdowns = document.querySelectorAll('[data-expiry-hours]');
        
        countdowns.forEach(element => {
            const oreRimanenti = parseFloat(element.dataset.expiryHours);
            const formatted = this.formatTimeRemaining(oreRimanenti);
            element.textContent = `⏰ Scade tra: ${formatted}`;
            
            // Cambia colore se sta per scadere
            if (oreRimanenti < 1) {
                element.style.color = '#ff4444';
                element.style.fontWeight = 'bold';
            } else if (oreRimanenti < 6) {
                element.style.color = '#ff9800';
            }
        });
    }

    formatTimeRemaining(ore) {
        if (ore < 0) return 'Scaduto';
        
        if (ore < 1) {
            const minuti = Math.floor(ore * 60);
            return `${minuti}m`;
        } else if (ore < 24) {
            const h = Math.floor(ore);
            const m = Math.floor((ore - h) * 60);
            return `${h}h ${m}m`;
        } else {
            const giorni = Math.floor(ore / 24);
            const h = Math.floor(ore % 24);
            return `${giorni}g ${h}h`;
        }
    }

    showNotification(message, type = 'info') {
        // Crea notifica toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    openChat(chatId) {
        window.location.href = `/chat/room/${chatId}`;
    }
}

// Inizializza quando DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    window.instantGroupsManager = new InstantGroupsManager();
});

// Funzioni globali per onclick handlers
function joinInstantGroup(chatId) {
    window.instantGroupsManager.joinGroup(chatId);
}

function leaveInstantGroup(chatId) {
    window.instantGroupsManager.leaveGroup(chatId);
}

function deleteInstantGroup(chatId) {
    window.instantGroupsManager.deleteGroup(chatId);
}

function openInstantGroupChat(chatId) {
    window.instantGroupsManager.openChat(chatId);
}
