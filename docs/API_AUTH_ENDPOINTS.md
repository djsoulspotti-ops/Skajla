# SKAILA - API Authentication Endpoints

Documentazione completa degli endpoint REST API per l'autenticazione.

## 🔐 Base URL

```
http://localhost:5000/api
```

**Nota:** Tutti gli endpoint usano autenticazione session-based (cookie), non JWT.

---

## 📋 Endpoint Disponibili

### 1. POST `/api/register`

Registra un nuovo utente.

**Request Body (JSON):**
```json
{
    "username": "mario.rossi",
    "email": "mario.rossi@example.com",
    "password": "SecurePass123!",
    "nome": "Mario",
    "cognome": "Rossi",
    "codice_scuola": "SKAIL-ABC123"
}
```

**Campi:**
- `username` (string, required) - Username univoco
- `email` (string, required) - Email valida RFC-compliant
- `password` (string, required) - Password forte (8+ chars, maiuscola, minuscola, numero, speciale)
- `nome` (string, required) - Nome
- `cognome` (string, required) - Cognome
- `codice_scuola` (string, optional) - Codice scuola per auto-assegnazione

**Success Response (201 Created):**
```json
{
    "success": true,
    "message": "Benvenuto Mario! Account creato con successo",
    "user": {
        "id": 123,
        "username": "mario.rossi",
        "email": "mario.rossi@example.com",
        "nome": "Mario",
        "cognome": "Rossi",
        "ruolo": "studente",
        "classe": "3A",
        "scuola_id": 5
    }
}
```

**Error Responses:**

400 Bad Request - Dati mancanti o non validi:
```json
{
    "success": false,
    "error": "Email non valida",
    "message": "Formato email non valido"
}
```

409 Conflict - Utente già esistente:
```json
{
    "success": false,
    "error": "Utente già esistente",
    "message": "Email o username già registrati"
}
```

---

### 2. POST `/api/login`

Autentica un utente esistente.

**Request Body (JSON):**
```json
{
    "email": "mario.rossi@example.com",
    "password": "SecurePass123!",
    "remember_me": true
}
```

**Campi:**
- `email` (string, required) - Email account
- `password` (string, required) - Password
- `remember_me` (boolean, optional) - Sessione lunga (30 giorni) vs breve (1 giorno)

**Success Response (200 OK):**
```json
{
    "success": true,
    "message": "Bentornato, Mario!",
    "user": {
        "id": 123,
        "username": "mario.rossi",
        "email": "mario.rossi@example.com",
        "nome": "Mario",
        "cognome": "Rossi",
        "ruolo": "studente",
        "classe": "3A",
        "avatar": "default.jpg",
        "scuola_id": 5
    }
}
```

**Error Responses:**

401 Unauthorized - Credenziali errate:
```json
{
    "success": false,
    "error": "Credenziali errate",
    "message": "Email o password non corretti"
}
```

429 Too Many Requests - Account bloccato:
```json
{
    "success": false,
    "error": "Account bloccato",
    "message": "Troppi tentativi falliti. Riprova tra 15 minuti",
    "locked_until_minutes": 15
}
```

---

### 3. POST `/api/logout`

Effettua logout (invalida sessione corrente).

**Headers:**
- Richiede autenticazione (sessione attiva)

**Request Body:**
Nessuno

**Success Response (200 OK):**
```json
{
    "success": true,
    "message": "Arrivederci, Mario!"
}
```

**Error Response:**

401 Unauthorized - Non autenticato:
```json
{
    "success": false,
    "error": "Non autenticato",
    "message": "Devi effettuare il login per accedere a questa risorsa"
}
```

---

### 4. GET `/api/user/me`

Restituisce dati dell'utente loggato (endpoint protetto).

**Headers:**
- Richiede autenticazione (sessione attiva)

**Success Response (200 OK):**
```json
{
    "success": true,
    "user": {
        "id": 123,
        "username": "mario.rossi",
        "email": "mario.rossi@example.com",
        "nome": "Mario",
        "cognome": "Rossi",
        "ruolo": "studente",
        "classe": "3A",
        "scuola_id": 5,
        "avatar": "default.jpg",
        "bio": "Studente appassionato di matematica",
        "xp": 1250,
        "livello": 5,
        "data_creazione": "2024-01-15T10:30:00",
        "gamification": {
            "xp_totale": 1250,
            "livello": 5,
            "streak_giorni": 7,
            "badge_count": 3
        }
    }
}
```

**Error Responses:**

401 Unauthorized:
```json
{
    "success": false,
    "error": "Non autenticato",
    "message": "Devi effettuare il login per accedere a questa risorsa"
}
```

404 Not Found - Sessione non valida:
```json
{
    "success": false,
    "error": "Utente non trovato",
    "message": "Sessione non valida"
}
```

---

## 🔒 Sicurezza

### Password Policy

Le password devono soddisfare questi requisiti:

- ✅ Minimo 8 caratteri
- ✅ Almeno una lettera maiuscola (A-Z)
- ✅ Almeno una lettera minuscola (a-z)
- ✅ Almeno un numero (0-9)
- ✅ Almeno un carattere speciale (!@#$%^&*...)
- ❌ Non deve essere una password comune
- ❌ Non deve contenere pattern sequenziali (123456, abcdef)

### Email Validation

Le email vengono validate secondo RFC 5322:

- ✅ Formato `locale@domain.tld`
- ✅ Parte locale max 64 caratteri
- ✅ Dominio valido con estensione
- ❌ Domini temporanei bloccati (tempmail.com, 10minutemail.com)

### Rate Limiting

- **Max tentativi login:** 5 tentativi falliti
- **Lockout duration:** 15 minuti
- **Countdown:** Messaggi con minuti rimanenti

### CORS

- **Development:** `Access-Control-Allow-Origin: *`
- **Production:** Origini limitate e whitelisted

---

## 📚 Esempi d'Uso

### JavaScript (Fetch API)

```javascript
// Login
async function login(email, password) {
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({ email, password, remember_me: true })
    });
    
    const data = await response.json();
    
    if (data.success) {
        console.log('Login riuscito:', data.user);
        window.location.href = '/dashboard';
    } else {
        alert('Errore: ' + data.message);
    }
}

// Get current user
async function getCurrentUser() {
    const response = await fetch('/api/user/me', {
        credentials: 'same-origin'
    });
    
    const data = await response.json();
    
    if (data.success) {
        console.log('User:', data.user);
        return data.user;
    }
}
```

### cURL

```bash
# Register
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test.user",
    "email": "test@example.com",
    "password": "TestPass123!",
    "nome": "Test",
    "cognome": "User"
  }'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Get current user (usa cookie salvato)
curl -X GET http://localhost:5000/api/user/me \
  -b cookies.txt

# Logout
curl -X POST http://localhost:5000/api/logout \
  -b cookies.txt
```

### Python (requests)

```python
import requests

BASE_URL = 'http://localhost:5000/api'
session = requests.Session()

# Login
response = session.post(f'{BASE_URL}/login', json={
    'email': 'test@example.com',
    'password': 'TestPass123!'
})

if response.json()['success']:
    print('Login riuscito!')
    
    # Get user info
    user_response = session.get(f'{BASE_URL}/user/me')
    user = user_response.json()['user']
    print(f"User: {user['nome']} {user['cognome']}")
```

---

## ✨ Note Implementative

1. **Session-based auth:** Usa cookie di sessione Flask, non JWT tokens
2. **Remember Me:** Sessioni lunghe (30 giorni) vs brevi (1 giorno)
3. **Auto-enrollment:** Studenti vengono automaticamente aggiunti alla chat di classe
4. **Gamification:** XP assegnato automaticamente al login
5. **CSRF Protection:** Già implementato per form HTML (API esenti se same-origin)

---

## 🚀 Deployment

Gli endpoint API sono pronti per production deployment con:

- ✅ Gunicorn + eventlet workers
- ✅ PostgreSQL connection pooling
- ✅ Security headers (HSTS, CSP, X-Content-Type-Options)
- ✅ CORS configurato per development/production
- ✅ Rate limiting su endpoint critici

---

**Documentazione aggiornata:** 27 Ottobre 2025  
**Version:** 1.0.0
