# 🛠️ Guida per Sviluppatori SKAJLA

## 📋 Panoramica Architettura

SKAJLA è un'applicazione Flask con architettura modulare che include:
- **Backend:** Flask + Socket.IO per comunicazione real-time
- **Database:** PostgreSQL (Neon) in produzione
- **AI Coach:** Sistema coaching personalizzato senza OpenAI
- **Gamification:** XP, livelli, badge
- **Multi-tenant:** Supporto per più scuole isolate

---

## 🚀 Come Avviare il Progetto

### Requisiti
- Python 3.11+
- PostgreSQL (fornito da Replit)

### Comandi Base
```bash
# Avvia il server di sviluppo
python main.py

# Il server sarà disponibile su http://localhost:5000
```

---

## 📁 Struttura del Progetto

```
skaila/
├── main.py                         # Entry point dell'applicazione
├── database_manager.py             # Gestione database PostgreSQL
├── gamification.py                 # Sistema XP e livelli
├── ai_chatbot.py                   # Chatbot AI SKAJLA Coach
├── coaching_engine.py              # Motore coaching soft skills
│
├── core/
│   └── config/
│       ├── settings.py             # Configurazioni app (SSoT)
│       └── gamification_config.py  # Config XP, badge, livelli
│
├── routes/                         # Blueprint delle rotte
│   ├── auth_routes.py              # Login, registrazione
│   ├── dashboard_routes.py         # Dashboard studenti/prof
│   ├── api_routes.py               # API REST
│   ├── messaging_routes.py         # Chat e messaggi
│   └── admin_routes.py             # Dashboard admin
│
├── shared/                         # Utilities condivise
│   ├── validators/
│   │   └── input_validators.py     # Validazione input (XSS, SQL injection)
│   └── formatters/
│       ├── date_formatters.py      # Formattazione date italiane
│       └── file_formatters.py      # Formattazione dimensioni file
│
├── services/
│   └── tenant_guard.py             # Sistema multi-tenant security
│
└── templates/                      # Template HTML
    ├── dashboard_studente.html
    ├── ai_chat.html
    ├── admin_dashboard.html
    └── ...
```

---

## ✏️ Come Apportare Modifiche

### 1️⃣ **Aggiungere una Nuova Route**

**Esempio: Creare endpoint per visualizzare statistiche studente**

```python
# File: routes/api_routes.py

@api_bp.route('/student/stats')
def student_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401
    
    try:
        # SECURITY: Tenant guard
        school_id = get_current_school_id()
        user_id = session['user_id']
        
        stats = db_manager.query('''
            SELECT 
                COUNT(*) as total_activities,
                AVG(voto) as avg_grade
            FROM voti 
            WHERE studente_id = %s
        ''', (user_id,), one=True)
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2️⃣ **Modificare il Database**

**IMPORTANTE:** Usa sempre query parametrizzate per sicurezza PostgreSQL

```python
# ✅ CORRETTO - Usa %s per parametri
db_manager.execute('''
    INSERT INTO utenti (nome, email) 
    VALUES (%s, %s)
''', (nome, email))

# ❌ SBAGLIATO - Mai concatenare stringhe (SQL injection!)
db_manager.execute(f"INSERT INTO utenti (nome) VALUES ('{nome}')")
```

### 3️⃣ **Aggiungere Nuove Azioni XP**

Modifica il file di configurazione centralizzato:

```python
# File: core/config/gamification_config.py

class XPConfig:
    XP_ACTIONS = {
        'ai_interaction': 10,        # Esistente
        'quiz_completed': 50,         # Esistente
        'homework_submitted': 30,     # NUOVO - Aggiungi qui
    }
```

Poi usa nel codice:

```python
from gamification import gamification_system

gamification_system.award_xp(
    user_id=session['user_id'],
    action_type='homework_submitted',
    description='Compiti di matematica consegnati'
)
```

### 4️⃣ **Modificare il Chatbot AI**

Il chatbot è un sistema di coaching che **NON richiede API esterne**.

```python
# File: ai_chatbot.py

# Per modificare le risposte, edita i template in coaching_engine.py
# Esempio: aggiungere nuovo template per ansia da esame

COACHING_TEMPLATES = {
    # ... template esistenti ...
    
    'exam_anxiety': {
        'trigger_words': ['esame', 'ansia', 'panico', 'paura'],
        'response_template': '''
        Capisco che gli esami possano generare ansia. 
        Ecco alcune tecniche per gestirla:
        
        1. 📝 Pianifica lo studio in anticipo
        2. 🧘 Pratica respirazione profonda
        3. 💪 Ricorda i tuoi successi passati
        
        Vuoi parlarne?
        '''
    }
}
```

### 5️⃣ **Aggiungere Nuove Pagine Template**

```python
# 1. Crea il template HTML
# File: templates/nuova_pagina.html
<!DOCTYPE html>
<html>
<head>
    <title>Nuova Pagina</title>
</head>
<body>
    <h1>{{ user.nome }}</h1>
</body>
</html>

# 2. Crea la route
# File: routes/dashboard_routes.py
@dashboard_bp.route('/nuova-pagina')
def nuova_pagina():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('nuova_pagina.html', user=session)
```

---

## 🔒 Sicurezza - REGOLE OBBLIGATORIE

### 1. **Sempre Verificare Autenticazione**
```python
if 'user_id' not in session:
    return jsonify({'error': 'Non autorizzato'}), 401
```

### 2. **Sempre Usare Tenant Guard per Multi-Tenant**
```python
from services.tenant_guard import get_current_school_id

school_id = get_current_school_id()

# Filtra sempre per scuola nelle query
db_manager.query('''
    SELECT * FROM chat 
    WHERE scuola_id = %s
''', (school_id,))
```

### 3. **Validazione Input**
```python
from shared.validators.input_validators import (
    validate_email, 
    validate_password,
    sanitize_text_input
)

# Valida sempre input utente
email = validate_email(request.form['email'])
password = validate_password(request.form['password'])
message = sanitize_text_input(request.form['message'])
```

### 4. **Mai Esporre Segreti**
```python
# ❌ SBAGLIATO
print(f"Database password: {os.getenv('DATABASE_PASSWORD')}")

# ✅ CORRETTO
# I segreti sono in variabili d'ambiente, mai loggarli
```

---

## 🧪 Testing

### Test Manuale
1. Accedi con credenziali test: `mario.rossi` / `password123`
2. Verifica funzionalità nella dashboard
3. Testa chatbot AI inviando messaggi
4. Controlla che XP vengano assegnati correttamente

### Test Database
```python
# Verifica connessione
python3 << EOF
from database_manager import db_manager
result = db_manager.query("SELECT COUNT(*) FROM utenti", one=True)
print(f"Utenti nel database: {result['count']}")
EOF
```

---

## ⚠️ Errori Comuni da Evitare

### ❌ **Route Duplicate**
```python
# NON creare file multipli con stesse route
# Esempio SBAGLIATO:
# File 1: api_routes.py ha @api_bp.route('/ai/chat')
# File 2: skaila_ai_routes.py ha @ai_bp.route('/api/ai/chat')
# Questo causa collisioni e server error 500
```

### ❌ **Tabelle Database Inesistenti**
```python
# Prima di fare query, verifica che la tabella esista
# Esempio: ai_conversations NON esiste più, ora si usa coaching_interactions

# SBAGLIATO
INSERT INTO ai_conversations ...

# CORRETTO
INSERT INTO coaching_interactions ...
```

### ❌ **Concatenazione SQL**
```python
# SBAGLIATO - SQL Injection vulnerability
query = f"SELECT * FROM utenti WHERE username='{username}'"

# CORRETTO - Query parametrizzata
query = "SELECT * FROM utenti WHERE username=%s"
db_manager.query(query, (username,))
```

---

## 🎯 Best Practices

### 1. **Single Source of Truth (SSoT)**
Tutte le configurazioni stanno in `core/config/`:
- Settings app → `settings.py`
- Config gamification → `gamification_config.py`

### 2. **Modularità**
- Una feature = un file
- Usa blueprint per organizzare route
- Separa business logic da presentation

### 3. **Naming Convention**
- File: `snake_case.py`
- Classi: `PascalCase`
- Funzioni: `snake_case()`
- Costanti: `UPPER_CASE`

### 4. **Commenti**
```python
# ✅ BUONO - Spiega il PERCHÉ
# SECURITY: Tenant guard previene accesso cross-school
school_id = get_current_school_id()

# ❌ CATTIVO - Spiega il COSA (già ovvio dal codice)
# Ottieni school_id
school_id = get_current_school_id()
```

---

## 🔧 Comandi Utili

### Riavvio Server
```bash
# Il server si riavvia automaticamente quando modifichi file Python
# Se devi riavviarlo manualmente:
pkill -f "python main.py" && python main.py
```

### Verificare Logs
```bash
# Controlla errori nel server
tail -f /tmp/logs/SKAJLA_Server_*.log
```

### Database Console
```bash
# Accedi a database PostgreSQL
psql $DATABASE_URL
```

---

## 📞 Workflow di Sviluppo Consigliato

1. **Analizza** cosa vuoi modificare
2. **Verifica** se esiste già codice simile (riusalo!)
3. **Crea** la modifica seguendo le best practices
4. **Testa** manualmente la funzionalità
5. **Controlla** i logs per errori
6. **Verifica** sicurezza (autenticazione, tenant guard, validazione)
7. **Commit** con messaggio chiaro

---

## 🆘 Problemi Comuni e Soluzioni

### Problema: "Server Error 500"
**Causa:** Route duplicate o tabella database inesistente  
**Soluzione:** Controlla logs, verifica route uniche

### Problema: "Non autorizzato (401)"
**Causa:** Sessione non valida  
**Soluzione:** Verifica che l'utente abbia fatto login, controlla `session['user_id']`

### Problema: "Module not found"
**Causa:** Dipendenza mancante  
**Soluzione:** Installa con `poetry add nome-pacchetto`

### Problema: "Database error"
**Causa:** Query SQL errata o tabella inesistente  
**Soluzione:** Verifica sintassi SQL PostgreSQL, usa query parametrizzate

---

## 📚 Riferimenti Tecnici

- **Flask Docs:** https://flask.palletsprojects.com/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Socket.IO:** https://socket.io/docs/
- **Replit Docs:** https://docs.replit.com/

---

## 🎓 Contatti e Supporto

Per domande o problemi, consulta:
1. Questa guida
2. File `replit.md` (documentazione architettura)
3. Commenti nel codice sorgente

**Ultima modifica:** 23 Ottobre 2025

---

## ✅ Checklist Pre-Deploy

Prima di pubblicare modifiche:

- [ ] Testato manualmente tutte le funzionalità modificate
- [ ] Verificato che non ci siano errori nei logs
- [ ] Controllato sicurezza (autenticazione, validazione input)
- [ ] Verificato compatibilità multi-tenant
- [ ] Aggiornato documentazione se necessario
- [ ] Codice pulito e commentato dove necessario
