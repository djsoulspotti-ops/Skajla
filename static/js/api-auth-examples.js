/**
 * SKAJLA API Authentication Examples
 * Esempi di utilizzo degli endpoint REST API
 */

// ==================== CONFIGURAZIONE ====================

const API_BASE_URL = window.location.origin + '/api';

// Helper per fetch con gestione errori
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(API_BASE_URL + endpoint, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Errore nella richiesta');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==================== REGISTRAZIONE ====================

async function apiRegister(userData) {
    /**
     * Registra un nuovo utente tramite API
     * 
     * @param {Object} userData - Dati utente
     * @param {string} userData.username - Username
     * @param {string} userData.email - Email
     * @param {string} userData.password - Password
     * @param {string} userData.nome - Nome
     * @param {string} userData.cognome - Cognome
     * @param {string} [userData.codice_scuola] - Codice scuola (opzionale)
     * 
     * @returns {Promise<Object>} Dati utente registrato
     */
    try {
        const result = await apiRequest('/register', 'POST', userData);
        
        console.log('✅ Registrazione riuscita:', result);
        
        return result;
    } catch (error) {
        console.error('❌ Errore registrazione:', error.message);
        throw error;
    }
}

// Esempio utilizzo registrazione
async function exampleRegister() {
    try {
        const result = await apiRegister({
            username: 'mario.rossi',
            email: 'mario.rossi@example.com',
            password: 'SecurePass123!',
            nome: 'Mario',
            cognome: 'Rossi',
            codice_scuola: 'SKAIL-ABC123'
        });
        
        alert(`Benvenuto ${result.user.nome}!`);
        window.location.href = '/dashboard';
    } catch (error) {
        alert('Errore: ' + error.message);
    }
}

// ==================== LOGIN ====================

async function apiLogin(email, password, rememberMe = false) {
    /**
     * Effettua login tramite API
     * 
     * @param {string} email - Email utente
     * @param {string} password - Password
     * @param {boolean} [rememberMe=false] - Remember me
     * 
     * @returns {Promise<Object>} Dati utente loggato
     */
    try {
        const result = await apiRequest('/login', 'POST', {
            email,
            password,
            remember_me: rememberMe
        });
        
        console.log('✅ Login riuscito:', result);
        
        return result;
    } catch (error) {
        console.error('❌ Errore login:', error.message);
        throw error;
    }
}

// Esempio utilizzo login
async function exampleLogin() {
    try {
        const result = await apiLogin(
            'studente.test@skaila.it',
            'test123',
            true
        );
        
        alert(`Bentornato ${result.user.nome}!`);
        window.location.href = '/dashboard';
    } catch (error) {
        alert('Errore: ' + error.message);
    }
}

// ==================== LOGOUT ====================

async function apiLogout() {
    /**
     * Effettua logout tramite API
     * 
     * @returns {Promise<Object>} Messaggio conferma
     */
    try {
        const result = await apiRequest('/logout', 'POST');
        
        console.log('✅ Logout riuscito:', result);
        
        return result;
    } catch (error) {
        console.error('❌ Errore logout:', error.message);
        throw error;
    }
}

// Esempio utilizzo logout
async function exampleLogout() {
    try {
        const result = await apiLogout();
        
        alert(result.message);
        window.location.href = '/login';
    } catch (error) {
        alert('Errore: ' + error.message);
    }
}

// ==================== GET USER INFO ====================

async function apiGetCurrentUser() {
    /**
     * Ottiene dati utente corrente
     * 
     * @returns {Promise<Object>} Dati utente completi
     */
    try {
        const result = await apiRequest('/user/me', 'GET');
        
        console.log('✅ Dati utente:', result);
        
        return result;
    } catch (error) {
        console.error('❌ Errore recupero dati utente:', error.message);
        throw error;
    }
}

// Esempio utilizzo get user
async function exampleGetUser() {
    try {
        const result = await apiGetCurrentUser();
        
        console.log('User ID:', result.user.id);
        console.log('Nome completo:', `${result.user.nome} ${result.user.cognome}`);
        console.log('Ruolo:', result.user.ruolo);
        console.log('XP:', result.user.gamification.xp_totale);
        console.log('Livello:', result.user.gamification.livello);
    } catch (error) {
        alert('Errore: ' + error.message);
    }
}

// ==================== INTEGRAZIONE CON FORM HTML ====================

function setupLoginForm() {
    /**
     * Setup automatico form login per usare API
     * Aggiunge event listener al form con id "loginForm"
     */
    const loginForm = document.getElementById('loginForm');
    
    if (!loginForm) return;
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = this.querySelector('[name="email"]').value;
        const password = this.querySelector('[name="password"]').value;
        const rememberMe = this.querySelector('[name="remember_me"]')?.checked || false;
        
        const submitBtn = this.querySelector('[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Accesso in corso...';
            
            const result = await apiLogin(email, password, rememberMe);
            
            window.location.href = '/dashboard';
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-error';
            errorDiv.textContent = '❌ ' + error.message;
            loginForm.insertBefore(errorDiv, loginForm.firstChild);
            
            setTimeout(() => errorDiv.remove(), 5000);
        }
    });
}

function setupRegisterForm() {
    /**
     * Setup automatico form registrazione per usare API
     * Aggiunge event listener al form con id "registerForm"
     */
    const registerForm = document.getElementById('registerForm');
    
    if (!registerForm) return;
    
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            nome: formData.get('nome'),
            cognome: formData.get('cognome'),
            codice_scuola: formData.get('codice_scuola_premium') || formData.get('codice_scuola')
        };
        
        const submitBtn = this.querySelector('[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Registrazione in corso...';
            
            const result = await apiRegister(userData);
            
            window.location.href = '/dashboard';
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-error';
            errorDiv.textContent = '❌ ' + error.message;
            registerForm.insertBefore(errorDiv, registerForm.firstChild);
            
            setTimeout(() => errorDiv.remove(), 5000);
        }
    });
}

// Auto-setup quando DOM è pronto
document.addEventListener('DOMContentLoaded', function() {
    // Decommentare per abilitare API automatica sui form
    // setupLoginForm();
    // setupRegisterForm();
    
    console.log('📡 SKAJLA API Auth disponibile');
    console.log('Endpoint disponibili:');
    console.log('  - POST /api/register');
    console.log('  - POST /api/login');
    console.log('  - POST /api/logout');
    console.log('  - GET /api/user/me');
});

// ==================== EXPORT (per moduli ES6) ====================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiRegister,
        apiLogin,
        apiLogout,
        apiGetCurrentUser,
        setupLoginForm,
        setupRegisterForm
    };
}
