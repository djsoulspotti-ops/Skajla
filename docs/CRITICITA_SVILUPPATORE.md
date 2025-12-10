# 🚨 CRITICITÀ DA RISOLVERE - SKAJLA

**Data analisi**: 24 Ottobre 2025  
**Gravità**: ⚠️ ALTA - Alcune criticità bloccanti per produzione

---

## ❌ CRITICITÀ GRAVI (URGENTI)

### 1. **SERVER NON SI AVVIAVA - FIXED**
**File**: `main.py` linea 284  
**Problema**: Chiamata metodo inesistente `keep_alive.keep_database_alive()`  
**Errore**: `AttributeError: 'KeepAliveService' object has no attribute 'keep_database_alive'`  
**Fix applicato**: Cambiato in `keep_alive.start()`  
**Status**: ✅ **RISOLTO**

---

### 2. **METODO MANCANTE - Storage Cleanup**
**File**: `database_keep_alive.py` linea 71  
**Problema**: Chiamata a `materials_manager.check_storage_usage()` ma il metodo NON ESISTE  
**Impatto**: Thread storage cleanup crasherà al primo ciclo (dopo 24h)  
**Fix richiesto**: 
```python
# In teaching_materials_manager.py aggiungi:
def check_storage_usage(self):
    """Verifica utilizzo storage e cleanup se necessario"""
    # TODO: Implementare logica
    return {
        'warning': False,
        'cleaned_files': 0,
        'total_gb': 0,
        'limit_gb': 10
    }
```
**Status**: ⚠️ **DA RISOLVERE**

---

### 3. **RACE CONDITION - Registrazione Premium Codes**
**File**: `routes/auth_routes.py` linee 125-175  
**Problema**: Due utenti che si registrano simultaneamente con lo stesso codice premium potrebbero creare scuole duplicate  
**Fix applicato**: Aggiunto `SELECT ... FOR UPDATE` lock transazionale  
**Verifica**: Testare con 2+ registrazioni simultanee dello stesso codice  
**Status**: ✅ **MITIGATO** (serve test di stress)

---

## ⚠️ CRITICITÀ MEDIE

### 4. **VALIDAZIONE INPUT INCOMPLETA**
**File**: `routes/auth_routes.py` linee 86-95  
**Problema**: 
- Nome/Cognome sanitizzati ma NO validazione lunghezza
- Username NON validato affatto
- Email validata solo nel login, non nella registrazione con codici premium
- Password: lunghezza minima solo lato client JavaScript

**Fix richiesto**:
```python
# Nel form registrazione, DOPO linea 93:
username = validator.sanitize_html(request.form['username'])
if not validator.validate_username(username):  # MANCANTE!
    flash('Username non valido', 'error')
    return render_template('register.html', ...)

# Validazione nomi
if len(nome) > 50 or len(cognome) > 50:  # MANCANTE!
    flash('Nome/Cognome troppo lunghi', 'error')
    return ...
```
**Status**: ⚠️ **DA RISOLVERE**

---

### 5. **SQL INJECTION PROTECTION PARZIALE**
**File**: Multipli  
**Problema**: `sql_protector.is_safe()` usato SOLO nel login, non in registrazione/altre routes  
**Rischio**: Medio (parametrizzazione presente ma protezione regex assente)  

**Fix richiesto**:
```python
# In TUTTE le routes che prendono input utente:
from shared.validators.input_validators import sql_protector

if not sql_protector.is_safe(email) or not sql_protector.is_safe(nome):
    flash('Input contiene caratteri non validi', 'error')
    return ...
```

**File da controllare**:
- `routes/messaging_routes.py` - send_message (contenuto chat)
- `routes/school_routes.py` - auto_register_school (nome scuola)
- `routes/admin_school_codes_routes.py` - tutti gli endpoint

**Status**: ⚠️ **DA RISOLVERE**

---

### 6. **MONITORING SYSTEM DISABILITATO**
**File**: `main.py` linee 304-317  
**Problema**: Sistema di monitoring temporaneamente disabilitato causa "eventlet mainloop blocking"  
**Impatto**: Zero visibilità su performance/errori in produzione  
**Fix richiesto**: 
- Implementare monitoring compatibile con eventlet
- Oppure usare Sentry/DataDog esterno

**Status**: ⚠️ **DA RISOLVERE**

---

### 7. **OPENAI_API_KEY MANCANTE**
**File**: Logs server  
**Problema**: AI chatbot in "mock mode" - NON funziona in produzione  
**Impatto**: Feature AI SKAJLA Coach completamente inutilizzabile  
**Fix richiesto**: 
1. Richiedere OPENAI_API_KEY all'utente
2. Configurare in secrets Replit
3. Testare integrazione OpenAI reale

**Status**: ⚠️ **DA RISOLVERE**

---

## 🔧 MIGLIORAMENTI CONSIGLIATI

### 8. **CODICE DUPLICATO - Coach Initialization**
**File**: Logs server (3 volte "✅ SKAJLA Coach inizializzato")  
**Problema**: Coaching engine viene inizializzato 3 volte  
**Fix**: Verifica `coaching_engine.py` e rimuovi inizializzazioni duplicate  
**Impatto**: Performance minimo ma codice confuso  

---

### 9. **EMAIL TEMPLATE NON IMPLEMENTATI**
**File**: `school_system.py` linea 667  
**Problema**: `# TODO: Integrazione SMTP reale per produzione`  
**Impatto**: Email invito dirigenti/professori NON vengono inviate  
**Fix richiesto**: Configurare SMTP (SendGrid/Mailgun/AWS SES)  

---

### 10. **LUNGHEZZA QUERY LOG**
**File**: `database_manager.py`  
**Problema**: Nessun logging query SQL in produzione  
**Fix richiesto**: Aggiungi query logging opzionale per debug (ma NON in prod per performance)

```python
def query(self, sql, params=None, one=False):
    if os.getenv('DEBUG_SQL') == 'true':
        print(f"[SQL] {sql[:100]}... params={params}")
    # ... resto del codice
```

---

### 11. **TEST MANCANTI**
**File**: Nessun file di test trovato  
**Problema**: ZERO test automatici  
**Impatto**: Impossibile verificare regressioni  
**Fix richiesto**: 
- Test registrazione con codici premium
- Test multi-tenant isolation
- Test gamification XP
- Test AI chatbot

**Framework consigliato**: pytest

---

### 12. **GESTIONE ERRORI GENERICA**
**File**: Multipli (try/except con solo print)  
**Problema**: Errori loggati ma NON tracciati/monitorati  
**Esempio**: `database_keep_alive.py` linea 78 - `print(f"⚠️ Storage cleanup error: {e}")`  

**Fix richiesto**: Usa logging strutturato + Sentry

```python
import logging
logger = logging.getLogger(__name__)

try:
    # codice
except Exception as e:
    logger.error(f"Storage cleanup failed: {e}", exc_info=True)
```

---

## 🔒 SICUREZZA

### 13. **PASSWORD POLICY DEBOLE**
**File**: `templates/register.html` linea 608  
**Problema**: Password minimo 6 caratteri, NO requisiti complessità  
**Fix richiesto**: 
- Minimo 8 caratteri
- Almeno 1 maiuscola, 1 numero
- Validazione lato server (non solo client)

---

### 14. **CSRF TOKEN - Verificare Copertura**
**File**: Multipli  
**Problema**: `@csrf_protect` presente ma non su TUTTE le routes POST  
**Fix richiesto**: Audit completo di tutte le routes POST/PUT/DELETE

---

### 15. **SECRET_KEY Storage**
**File**: `.env.secrets` (file locale)  
**Problema**: Secret key salvata in file non tracciato da git (BENE) ma non in vault produzione  
**Fix richiesto**: In produzione usare Replit Secrets o AWS Secrets Manager

---

## 📊 PERFORMANCE

### 16. **DATABASE INDEXES - Verificare Coverage**
**File**: `database_manager.py` - `create_optimized_indexes()`  
**Problema**: Indici creati ma non documentati quali tabelle/colonne  
**Fix richiesto**: Documento quali indici esistono + EXPLAIN ANALYZE query lente  

---

### 17. **N+1 QUERIES POTENZIALI**
**File**: Da verificare nelle dashboard (studente/professore/admin)  
**Problema**: Loop che fanno query singole invece di batch  
**Fix richiesto**: Usa JOIN o query batch invece di loop con query singole  

---

### 18. **CACHE REDIS - Non Utilizzata**
**File**: Logs - "✅ Sistema caching produzione inizializzato"  
**Problema**: Cache inizializzata ma NON sembra utilizzata nel codice  
**Fix richiesto**: Implementare caching per:
- Dati scuola (raramente cambiano)
- Gamification leaderboard
- Dashboard analytics

---

## 🗂️ ARCHITETTURA

### 19. **FILE GIGANTI**
**File**: `main.py` - 651 righe  
**Problema**: Troppo codice in un singolo file  
**Fix richiesto**: Splittare in:
- `app_factory.py` - creazione app
- `routes_registry.py` - registrazione blueprints
- `middleware.py` - CORS, CSRF, rate limiting

---

### 20. **DOCUMENTAZIONE CODICE CARENTE**
**Problema**: Funzioni complesse senza docstring  
**Esempio**: `routes/auth_routes.py` - logica codici premium NO docstring  
**Fix richiesto**: Aggiungi docstring Google-style

```python
def register():
    """
    Registrazione utente con supporto codici scuola premium.
    
    Priorità:
    1. Codice premium (SKAIL/PROF/DIR) -> crea/associa scuola
    2. Codice personale -> pre-assegnato
    3. Selezione manuale scuola
    
    Returns:
        redirect: Dashboard se successo
        template: Form registrazione se errore
    """
```

---

## 📱 FRONTEND

### 21. **VALIDAZIONE PASSWORD CLIENT-SIDE DUPLICATA**
**File**: `templates/register.html` linee 598-617 + 633-650  
**Problema**: Stessa validazione password scritta DUE VOLTE  
**Fix**: Unifica in una funzione JavaScript

---

### 22. **ACCESSIBILITY MANCANTE**
**File**: Tutti i template HTML  
**Problema**: NO aria-labels, NO focus management, NO screen-reader support  
**Fix richiesto**: 
- Aggiungi `aria-label` su input
- `role="alert"` su messaggi errore
- Focus automatico su primo campo con errore

---

## 🚀 DEPLOYMENT

### 23. **ENVIRONMENT VARIABLES NON DOCUMENTATE**
**File**: Nessun `.env.example`  
**Problema**: Sviluppatore nuovo non sa quali variabili servono  
**Fix richiesto**: Crea `.env.example` con tutte le var obbligatorie/opzionali

---

### 24. **BACKUP DATABASE - Non Configurato**
**Problema**: Nessun sistema backup automatico  
**Fix richiesto**: 
- Backup PostgreSQL giornaliero
- Retention policy (7 giorni)
- Test restore mensile

---

### 25. **HEALTH CHECK ENDPOINT MANCANTE**
**File**: Nessuno  
**Problema**: Nessun endpoint `/health` per monitoring esterno  
**Fix richiesto**: 

```python
@app.route('/health')
def health():
    try:
        db_manager.query('SELECT 1', one=True)
        return jsonify({'status': 'ok', 'db': 'connected'}), 200
    except:
        return jsonify({'status': 'error', 'db': 'disconnected'}), 503
```

---

## 📋 PRIORITÀ FIX

### 🔴 URGENTE (Blocca produzione):
1. ✅ ~~Server non si avvia~~ - **RISOLTO**
2. ⚠️ Metodo storage cleanup mancante
3. ⚠️ OPENAI_API_KEY per AI chatbot
4. ⚠️ Validazione input completa
5. ⚠️ Test registrazione codici premium

### 🟡 IMPORTANTE (Risolvere prima del lancio):
6. SQL injection protection completa
7. Monitoring system funzionante
8. Email SMTP configurato
9. Password policy robusta
10. Test automatici base

### 🟢 MIGLIORAMENTI (Post-lancio):
11. Performance optimization (N+1, cache)
12. Refactoring architettura (file giganti)
13. Documentazione completa
14. Accessibility frontend
15. Backup automatici

---

## ✅ CHECKLIST PRE-PRODUZIONE

- [ ] Fix metodo `check_storage_usage()`
- [ ] Configurare OPENAI_API_KEY
- [ ] Validazione input completa su tutte le routes
- [ ] Test stress registrazione simultanea
- [ ] SQL injection audit completo
- [ ] Configurare SMTP email reali
- [ ] Password policy minimo 8 caratteri
- [ ] Test automatici critici (registrazione, login, gamification)
- [ ] Health check endpoint
- [ ] Monitoring production (Sentry o similare)
- [ ] Backup database automatico
- [ ] Documentare environment variables
- [ ] Load testing (100+ utenti simultanei)

---

**TOTALE CRITICITÀ**: 25 trovate  
**BLOCKERS**: 2 (1 risolto, 1 residuo)  
**WARNINGS**: 8  
**IMPROVEMENTS**: 15  

**RACCOMANDAZIONE FINALE**: Il sistema è **funzionante** ma NON pronto per produzione senza risolvere almeno le criticità URGENTI (1-5).
