# 📚 API REGISTRO ELETTRONICO - SKAILA

**Documentazione completa degli endpoint API per gestione voti, presenze, note e calendario**

---

## 🔐 AUTENTICAZIONE

Tutti gli endpoint richiedono autenticazione. L'utente deve essere loggato (cookie di sessione valido).

**Autorizzazioni**:
- **Studenti**: Possono vedere solo i propri dati
- **Professori**: Possono inserire voti/presenze/note e vedere tutti gli studenti della propria classe
- **Dirigenti**: Accesso completo a tutti i dati della scuola

---

## 📋 ENDPOINT API

### **1. GESTIONE PRESENZE**

#### **POST** `/api/registro/presenze/segna`
Segna presenza/assenza per un singolo studente.

**Autorizzazione**: Solo professori/dirigenti

**Body**:
```json
{
  "student_id": 123,
  "date": "2025-10-24",
  "status": "presente",
  "note": "Opzionale"
}
```

**Status possibili**: `presente`, `assente`, `ritardo`, `uscita_anticipata`

**Risposta**:
```json
{
  "success": true,
  "message": "Presenza segnata: presente"
}
```

---

#### **POST** `/api/registro/presenze/classe`
Segna presenze per tutta la classe in un colpo solo.

**Autorizzazione**: Solo professori/dirigenti

**Body**:
```json
{
  "classe": "3A",
  "date": "2025-10-24",
  "attendance_list": [
    {"student_id": 1, "status": "presente", "note": ""},
    {"student_id": 2, "status": "assente", "note": "Malattia"},
    {"student_id": 3, "status": "ritardo", "note": "Traffico"}
  ]
}
```

**Risposta**:
```json
{
  "marked": 3,
  "errors": []
}
```

---

#### **GET** `/api/registro/presenze/studente/<student_id>`
Ottieni storico presenze di uno studente (ultimi 3 mesi).

**Autorizzazione**: Studente può vedere solo le sue, prof/dirigente tutte

**Risposta**:
```json
{
  "presenze": [
    {
      "date": "2025-10-24",
      "status": "presente",
      "note": "",
      "teacher": "Mario Rossi"
    },
    {
      "date": "2025-10-23",
      "status": "assente",
      "note": "Malattia",
      "teacher": "Luigi Bianchi"
    }
  ],
  "statistiche": {
    "totale_giorni": 60,
    "presenze": 55,
    "assenze": 5,
    "ritardi": 2,
    "percentuale_presenza": 91.7,
    "assenze_non_giustificate": 1
  }
}
```

---

### **2. GESTIONE VOTI**

#### **POST** `/api/registro/voti/inserisci`
Inserisci voto per uno studente.

**Autorizzazione**: Solo professori/dirigenti

**Body**:
```json
{
  "student_id": 123,
  "subject": "Matematica",
  "grade": 7.5,
  "evaluation_type": "scritto",
  "description": "Verifica algebra",
  "date": "2025-10-24"
}
```

**Parametri**:
- `grade`: Voto scala 1-10 (italiano)
- `evaluation_type`: `scritto` o `orale`
- `date`: Opzionale (default: oggi)

**Risposta**:
```json
{
  "success": true,
  "message": "Voto inserito con successo"
}
```

---

#### **GET** `/api/registro/voti/studente/<student_id>`
Ottieni voti e medie di uno studente (ultimi 6 mesi).

**Autorizzazione**: Studente può vedere solo i suoi, prof/dirigente tutti

**Risposta**:
```json
{
  "voti": [
    {
      "id": 456,
      "subject": "Matematica",
      "grade": 7.5,
      "evaluation_type": "scritto",
      "description": "Verifica algebra",
      "date": "2025-10-24",
      "teacher": "Prof. Rossi"
    },
    {
      "id": 457,
      "subject": "Italiano",
      "grade": 8.0,
      "evaluation_type": "orale",
      "description": "Interrogazione Dante",
      "date": "2025-10-23",
      "teacher": "Prof. Bianchi"
    }
  ],
  "medie": [
    {"subject": "Matematica", "average": 7.2},
    {"subject": "Italiano", "average": 8.1},
    {"subject": "Storia", "average": 6.8}
  ]
}
```

---

### **3. NOTE DISCIPLINARI**

#### **POST** `/api/registro/note/inserisci`
Inserisci nota disciplinare per uno studente.

**Autorizzazione**: Solo professori/dirigenti

**Body**:
```json
{
  "student_id": 123,
  "description": "Disturbo durante lezione",
  "severity": "lieve",
  "date": "2025-10-24"
}
```

**Severity**: `lieve`, `media`, `grave`

**Risposta**:
```json
{
  "success": true,
  "message": "Nota inserita"
}
```

---

#### **GET** `/api/registro/note/studente/<student_id>`
Ottieni note disciplinari di uno studente.

**Autorizzazione**: Studente può vedere solo le sue, prof/dirigente tutte

**Risposta**:
```json
{
  "note": [
    {
      "id": 789,
      "date": "2025-10-24",
      "description": "Disturbo durante lezione",
      "severity": "lieve",
      "teacher": "Prof. Rossi"
    }
  ]
}
```

---

### **4. CALENDARIO LEZIONI**

#### **POST** `/api/registro/lezioni/aggiungi`
Aggiungi lezione al calendario classe.

**Autorizzazione**: Solo professori/dirigenti

**Body**:
```json
{
  "class": "3A",
  "subject": "Matematica",
  "topic": "Equazioni di secondo grado",
  "homework": "Esercizi pag. 120-125",
  "lesson_date": "2025-10-24"
}
```

**Risposta**:
```json
{
  "success": true,
  "message": "Lezione aggiunta"
}
```

---

#### **GET** `/api/registro/lezioni/classe/<classe>`
Ottieni calendario lezioni di una classe (ultimo mese).

**Autorizzazione**: Studenti della classe, prof/dirigenti

**Risposta**:
```json
{
  "lezioni": [
    {
      "id": 101,
      "subject": "Matematica",
      "topic": "Equazioni di secondo grado",
      "homework": "Esercizi pag. 120-125",
      "lesson_date": "2025-10-24",
      "teacher": "Prof. Rossi"
    }
  ]
}
```

---

### **5. STATISTICHE COMPLETE**

#### **GET** `/api/registro/statistiche/studente/<student_id>`
Report completo studente (voti + presenze + note + statistiche).

**Autorizzazione**: Studente può vedere solo il suo, prof/dirigente tutti

**Risposta**:
```json
{
  "student": {
    "id": 123,
    "nome": "Mario",
    "cognome": "Rossi",
    "classe": "3A"
  },
  "attendance": {
    "totale_giorni": 60,
    "presenze": 55,
    "assenze": 5,
    "ritardi": 2,
    "percentuale_presenza": 91.7,
    "assenze_non_giustificate": 1
  },
  "subject_averages": [
    {"subject": "Matematica", "average": 7.2, "status": "sufficiente"},
    {"subject": "Italiano", "average": 8.1, "status": "buono"},
    {"subject": "Storia", "average": 5.8, "status": "insufficiente"}
  ],
  "disciplinary_notes_count": 2,
  "overall_status": "buono"
}
```

---

## 🔒 SICUREZZA

Ogni endpoint implementa:

1. **Autenticazione**: Verifica sessione utente
2. **Autorizzazione**: Controllo ruolo (studente/professore/dirigente)
3. **Tenant Isolation**: Verifica che utente appartenga alla scuola corretta
4. **Input Validation**: Sanitizzazione HTML + protezione SQL injection
5. **Parametrized Queries**: Tutte le query usano parametri, nessun concatenamento stringhe

---

## 📝 ESEMPI INTEGRAZIONE

### **JavaScript (Frontend)**

```javascript
// Inserisci voto
async function inserisciVoto(studentId, subject, grade) {
  const response = await fetch('/api/registro/voti/inserisci', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      student_id: studentId,
      subject: subject,
      grade: grade,
      evaluation_type: 'scritto',
      description: 'Verifica',
      date: new Date().toISOString().split('T')[0]
    })
  });
  
  const data = await response.json();
  if (data.success) {
    alert('Voto inserito!');
  } else {
    alert('Errore: ' + data.error);
  }
}

// Ottieni voti studente
async function getVotiStudente(studentId) {
  const response = await fetch(`/api/registro/voti/studente/${studentId}`);
  const data = await response.json();
  
  console.log('Voti:', data.voti);
  console.log('Medie:', data.medie);
}
```

---

### **Python (Backend Testing)**

```python
import requests

# Test inserimento presenza
def test_presenze():
    url = 'http://localhost:5000/api/registro/presenze/segna'
    data = {
        'student_id': 123,
        'date': '2025-10-24',
        'status': 'presente',
        'note': ''
    }
    
    # Cookie di sessione necessario
    response = requests.post(url, json=data, cookies={'session': 'your_session_cookie'})
    print(response.json())
```

---

## ❌ GESTIONE ERRORI

### **Errori comuni**:

```json
// 401 Unauthorized - Non loggato
{
  "error": "Non autenticato"
}

// 403 Forbidden - Permessi insufficienti
{
  "error": "Accesso negato - Solo professori"
}

// 404 Not Found - Studente non trovato
{
  "error": "Studente non trovato"
}

// 400 Bad Request - Parametri mancanti
{
  "error": "Parametri mancanti"
}

// 400 Bad Request - Voto non valido
{
  "error": "Voto deve essere tra 1 e 10"
}

// 500 Internal Server Error - Errore server
{
  "error": "Database connection failed"
}
```

---

## ✅ STATO IMPLEMENTAZIONE

- [x] **10 endpoint API** creati e funzionanti
- [x] **Autenticazione** + **Autorizzazione** implementate
- [x] **Tenant isolation** garantita
- [x] **Input validation** completa
- [x] **SQL injection protection**
- [x] **Error handling** robusto
- [x] **Blueprint registrato** in main.py
- [x] **Server testato** e funzionante

---

## 🚀 PROSSIMI PASSI

1. **Frontend**: Creare interfacce HTML per inserimento voti/presenze
2. **Export PDF**: Aggiungere endpoint per esportare pagelle in PDF
3. **Notifiche**: Inviare email ai genitori per nuovi voti/note
4. **Analytics**: Dashboard statistiche aggregate per dirigenti

---

**Data creazione**: 24 Ottobre 2025  
**File**: `routes/registro_routes.py`  
**Status**: ✅ **PRODUCTION READY**
