# SKAJLA Beta Test Credentials

Documento credenziali per il testing dell'applicazione SKAJLA in versione beta.

---

## Accesso Rapido

| Ruolo | Email | Password | Dashboard |
|-------|-------|----------|-----------|
| Studente | `studente@skaila.test` | `test123` | `/dashboard` |
| Professore | `professore@skaila.test` | `prof123` | `/dashboard/docente` |
| Dirigente | `dirigente@skaila.test` | `dirig123` | `/dashboard/dirigente` |
| Genitore | `genitore@skaila.test` | `parent123` | `/dashboard/genitore` |
| Admin | `admin@skaila.it` | `admin123` | `/admin` |

---

## Account Dettagliati per Ruolo

### Studenti

| Username | Email | Password | Nome | Cognome | Classe | Scuola |
|----------|-------|----------|------|---------|--------|--------|
| `studente_test` | `studente@skaila.test` | `test123` | Marco | Studente | 3A | Liceo Scientifico Demo |
| `alice_demo` | `alice@test.skaila.it` | `test123` | Alice | Demo | 3A | Liceo Scientifico Demo |
| `mario.rossi` | `test@skaila.edu` | `test123` | Mario | Rossi | 3A | Liceo Scientifico Demo |

**Funzionalita testabili:**
- Dashboard studente con voti e presenze
- AI Coach (chat con Gemini 2.0)
- Sistema Gamification (XP, rank, sfide, badge)
- Calendario personale
- Messaggistica real-time
- Quiz adattivi curriculum italiano

---

### Professori / Docenti

| Username | Email | Password | Nome | Cognome | Materia | Scuola |
|----------|-------|----------|------|---------|---------|--------|
| `professore_test` | `professore@skaila.test` | `prof123` | Anna | Docenti | Matematica | Liceo Scientifico Demo |
| `prof_test` | `prof.test@skaila.it` | `prof123` | Maria | Bianchi | Matematica | Liceo Scientifico Demo |
| `prof_demo` | `prof@test.skaila.it` | `prof123` | Prof | Demo | Tutte | Liceo Scientifico Demo |

**Funzionalita testabili:**
- Dashboard docente con overview classi
- Registro elettronico (voti, presenze)
- Early Warning System (studenti in difficolta)
- Messaggistica con studenti e genitori
- Annunci broadcast per classe
- Gestione compiti e verifiche

---

### Dirigenti Scolastici

| Username | Email | Password | Nome | Cognome | Scuola |
|----------|-------|----------|------|---------|--------|
| `dirigente_test` | `dirigente@skaila.test` | `dirig123` | Maria | Preside | Liceo Scientifico Demo |

**Funzionalita testabili:**
- Dashboard executive con KPI
- Overview scuola (studenti, docenti, classi)
- Analytics classi (medie voti, frequenze)
- Rating anonimi docenti
- KPI economici
- Engagement piattaforma
- Annunci broadcast scuola

---

### Genitori

| Username | Email | Password | Nome | Cognome | Figli |
|----------|-------|----------|------|---------|-------|
| `genitore_test` | `genitore@skaila.test` | `parent123` | Luigi | Genitori | Marco Studente |
| `papa` | `papa@skaila.it` | `papa123` | Papa | Famiglia | - |
| `mamma` | `mamma@skaila.it` | `mamma123` | Mamma | Famiglia | - |

**Funzionalita testabili:**
- Dashboard genitore (monitoraggio figli)
- Voti e presenze in tempo reale
- Comunicazioni con docenti
- Calendario eventi scolastici
- Notifiche automatiche

---

### Amministratori

| Username | Email | Password | Nome | Cognome | Livello |
|----------|-------|----------|------|---------|---------|
| `admin` | `admin@skaila.it` | `admin123` | Admin | SKAJLA | Super Admin |
| `founder` | `founder@skaila.it` | `founder123` | Daniele | Founder | Founder |
| `dev_support` | `dev.support@skaila.it` | `dev2024!` | Alex | Developer | Developer |

**Funzionalita testabili:**
- Pannello amministrazione
- Gestione scuole multi-tenant
- Gestione utenti globale
- Feature flags
- Monitoraggio sistema

---

## Demo Routes (Senza Login)

Per testare rapidamente le funzionalita senza autenticazione:

| Funzionalita | URL | Descrizione |
|--------------|-----|-------------|
| Homepage | `/` | Landing page principale |
| Dashboard Studente | `/demo/dashboard/studente` | Preview dashboard studente |
| Dashboard Docente | `/demo/dashboard/professore` | Preview dashboard docente |
| Dashboard Dirigente | `/demo/dashboard/dirigente` | Preview dashboard dirigente |
| AI Chat Demo | `/demo/ai-chat` | Pagina chatbot AI |
| AI Chat API | `POST /demo/ai/chat` | API chatbot (JSON) |
| Gamification | `/demo/gamification` | Preview sistema gamification |
| Messaggistica | `/demo/chat` | Preview hub messaggi |
| Calendario | `/demo/calendario` | Preview calendario |
| API Docs | `/api/docs` | Documentazione Swagger API |

---

## Informazioni Scuola Demo

**Nome:** Liceo Scientifico Demo  
**ID:** 1  
**Codice Pubblico:** `DEMO2024`  
**Codice Docenti:** `PROF2024`  
**Codice Dirigente:** `DIRIG2024`

### Classi Disponibili

| Classe | Studenti | Docente Coordinatore |
|--------|----------|---------------------|
| 3A | Marco, Alice, Mario | Prof. Anna Docenti |
| 4B | - | - |
| 5C | - | - |

---

## Note per i Beta Tester

### Suggerimenti Test

1. **Multi-ruolo**: Apri browser diversi (o finestre in incognito) per testare interazioni tra ruoli
2. **Messaggistica**: Testa la chat real-time tra studente e professore
3. **AI Coach**: Fai domande di studio al chatbot e verifica le risposte
4. **Gamification**: Completa sfide e verifica assegnazione XP/badge
5. **Mobile**: Testa la PWA su dispositivo mobile

### Segnalazione Bug

Per segnalare bug o problemi durante il beta test:
- Screenshot del problema
- Ruolo/account utilizzato
- Passi per riprodurre il bug
- Browser e dispositivo

### Limiti Beta

- Rate limiting: max 30 messaggi/minuto
- AI Chat: max 50 interazioni/giorno per utente
- Storage: max 10MB upload per file

---

## Credenziali JSON (per automazione)

```json
{
  "students": [
    {"email": "studente@skaila.test", "password": "test123", "name": "Marco Studente"},
    {"email": "alice@test.skaila.it", "password": "test123", "name": "Alice Demo"}
  ],
  "teachers": [
    {"email": "professore@skaila.test", "password": "prof123", "name": "Anna Docenti"},
    {"email": "prof.test@skaila.it", "password": "prof123", "name": "Maria Bianchi"}
  ],
  "principals": [
    {"email": "dirigente@skaila.test", "password": "dirig123", "name": "Maria Preside"}
  ],
  "parents": [
    {"email": "genitore@skaila.test", "password": "parent123", "name": "Luigi Genitori"}
  ],
  "admins": [
    {"email": "admin@skaila.it", "password": "admin123", "name": "Admin SKAJLA"}
  ]
}
```

---

**Ultimo aggiornamento:** Dicembre 2025  
**Versione:** Beta 1.0
