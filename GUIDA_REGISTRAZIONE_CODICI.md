# 📋 GUIDA REGISTRAZIONE ESTERNA - SKAILA

**Come far registrare persone esterne alla piattaforma SKAILA usando i codici scuola**

---

## 🎯 CODICI DISPONIBILI (10 Scuole Partner)

### **SCUOLA #1: Scuola Partner 1**
- **📚 Codice Studenti**: `SKAIL01904`
- **👨‍🏫 Codice Professori**: `PROF01THH9`
- **🎯 Codice Dirigente**: `DIR016FS87J`

### **SCUOLA #2: Scuola Partner 2**
- **📚 Codice Studenti**: `SKAIL02572`
- **👨‍🏫 Codice Professori**: `PROF022HXL`
- **🎯 Codice Dirigente**: `DIR02VD5QM4`

### **SCUOLA #3: Scuola Partner 3**
- **📚 Codice Studenti**: `SKAIL03829`
- **👨‍🏫 Codice Professori**: `PROF037J5Y`
- **🎯 Codice Dirigente**: `DIR037CNLK6`

### **SCUOLA #4: Scuola Partner 4**
- **📚 Codice Studenti**: `SKAIL04650`
- **👨‍🏫 Codice Professori**: `PROF04QZHZ`
- **🎯 Codice Dirigente**: `DIR04OZA1WA`

### **SCUOLA #5: Scuola Partner 5**
- **📚 Codice Studenti**: `SKAIL05245`
- **👨‍🏫 Codice Professori**: `PROF05UI9M`
- **🎯 Codice Dirigente**: `DIR05UWVSZE`

### **SCUOLA #6: Scuola Partner 6**
- **📚 Codice Studenti**: `SKAIL06502`
- **👨‍🏫 Codice Professori**: `PROF06VZ53`
- **🎯 Codice Dirigente**: `DIR060M9OGU`

### **SCUOLA #7: Scuola Partner 7**
- **📚 Codice Studenti**: `SKAIL07509`
- **👨‍🏫 Codice Professori**: `PROF07ZQ1S`
- **🎯 Codice Dirigente**: `DIR07HVE6DC`

### **SCUOLA #8: Scuola Partner 8**
- **📚 Codice Studenti**: `SKAIL08715`
- **👨‍🏫 Codice Professori**: `PROF08LKIC`
- **🎯 Codice Dirigente**: `DIR08JE52Y9`

### **SCUOLA #9: Scuola Partner 9**
- **📚 Codice Studenti**: `SKAIL09716`
- **👨‍🏫 Codice Professori**: `PROF096FHL`
- **🎯 Codice Dirigente**: `DIR09TGZHYU`

### **SCUOLA #10: Scuola Partner 10**
- **📚 Codice Studenti**: `SKAIL10473`
- **👨‍🏫 Codice Professori**: `PROF1013VL`
- **🎯 Codice Dirigente**: `DIR10EXNA1O`

---

## 🚀 ISTRUZIONI PER REGISTRAZIONE

### **PER STUDENTI**

1. Vai su: **http://localhost:5000/register** (o il tuo URL pubblico)

2. Compila il form:
   - **Nome**: Il tuo nome
   - **Cognome**: Il tuo cognome
   - **Email**: La tua email personale
   - **Password**: Minimo 6 caratteri
   - **Conferma Password**: Ripeti la password
   - **🎫 Codice Scuola**: Inserisci il codice `SKAIL` della tua scuola (es. `SKAIL01904`)
   - **Nome Classe**: Es. "3A", "Prima Liceo" (opzionale)

3. Clicca **"Inizia l'Avventura"**

4. ✅ **Fatto!** Sei registrato come studente e puoi accedere.

---

### **PER PROFESSORI**

1. Vai su: **http://localhost:5000/register**

2. Compila il form:
   - **Nome**: Il tuo nome
   - **Cognome**: Il tuo cognome
   - **Email**: La tua email
   - **Password**: Minimo 6 caratteri
   - **Conferma Password**: Ripeti la password
   - **🎫 Codice Scuola**: Inserisci il codice `PROF` della tua scuola (es. `PROF01THH9`)
   - **Nome Classe**: La classe che insegni (opzionale)

3. Clicca **"Inizia l'Avventura"**

4. ✅ **Fatto!** Sei registrato come professore.

---

### **PER DIRIGENTI SCOLASTICI**

1. Vai su: **http://localhost:5000/register**

2. Compila il form:
   - **Nome**: Il tuo nome
   - **Cognome**: Il tuo cognome
   - **Email**: La tua email
   - **Password**: Minimo 6 caratteri
   - **Conferma Password**: Ripeti la password
   - **🎫 Codice Scuola**: Inserisci il codice `DIR` della tua scuola (es. `DIR016FS87J`)

3. Clicca **"Inizia l'Avventura"**

4. ✅ **Fatto!** Sei registrato come dirigente con privilegi amministrativi.

---

## 💡 COME FUNZIONA

### **Sistema Automatico**

1. **Inserisci il codice** → Il sistema lo verifica nel database
2. **Prima registrazione** → Crea automaticamente la scuola
3. **Registrazioni successive** → Associa alla scuola esistente
4. **Ruolo automatico** → Assegnato in base al tipo di codice:
   - `SKAIL` → **Studente**
   - `PROF` → **Professore**
   - `DIR` → **Dirigente**

### **Vantaggi**

✅ **Nessuna configurazione manuale** - La scuola si crea da sola  
✅ **Codici sicuri** - Univoci e non indovinabili  
✅ **Illimitati utenti** - Per ogni scuola  
✅ **Ruoli automatici** - Nessun errore di assegnazione  

---

## 🔐 SICUREZZA

- Ogni codice è **univoco** e **generato casualmente**
- Alla prima registrazione, il codice viene **marcato come assegnato**
- Impossibile riutilizzare un codice per creare scuole duplicate
- I codici sono salvati nel database criptato

---

## 📧 CONDIVISIONE CODICI

### **Email Template per Studenti**

```
Oggetto: Benvenuto su SKAILA - Il tuo codice di accesso

Ciao!

Benvenuto sulla piattaforma educativa SKAILA 🚀

Il tuo codice scuola è: SKAIL01904

Per registrarti:
1. Vai su http://localhost:5000/register
2. Compila il form con i tuoi dati
3. Inserisci il codice: SKAIL01904
4. Clicca "Inizia l'Avventura"

Ci vediamo in piattaforma!
Team SKAILA
```

### **Email Template per Professori**

```
Oggetto: SKAILA - Codice Accesso Docenti

Gentile Professore/Professoressa,

Benvenuto sulla piattaforma SKAILA.

Il suo codice docente è: PROF01THH9

Per registrarsi:
1. http://localhost:5000/register
2. Inserire il codice: PROF01THH9
3. Completare la registrazione

Con questo codice avrà accesso alle funzionalità docente.

Cordiali saluti,
Team SKAILA
```

---

## ❓ DOMANDE FREQUENTI

### **Posso condividere il codice studenti con tutta la classe?**
Sì! Il codice `SKAIL` può essere usato da **tutti gli studenti** della stessa scuola.

### **Cosa succede se uso il codice sbagliato?**
Riceverai un errore: "Codice scuola non valido". Riprova con il codice corretto.

### **Posso cambiare scuola dopo la registrazione?**
Attualmente no. Il codice scuola è permanente.

### **Quanti utenti possono usare lo stesso codice?**
**Illimitati!** Ogni scuola può avere infiniti studenti, professori e dirigenti.

---

## 🛠️ AMMINISTRAZIONE

### **Controllare codici disponibili**

```bash
python3 << 'EOF'
from services.school_codes_manager import school_codes_manager
disponibili = school_codes_manager.get_available_codes_count()
print(f"Codici disponibili: {disponibili}/10")
EOF
```

### **Vedere tutte le scuole create**

```bash
python3 << 'EOF'
from database_manager import db_manager
scuole = db_manager.query("SELECT id, nome, codice_pubblico FROM scuole")
for s in scuole:
    print(f"ID: {s['id']} | Nome: {s['nome']} | Codice: {s['codice_pubblico']}")
EOF
```

---

## 📊 STATO SISTEMA

- **Codici generati**: 10 scuole
- **Codici disponibili**: 10
- **Sistema**: ✅ Operativo
- **Database**: PostgreSQL (Neon)

---

**Buon lavoro con SKAILA! 🎓**
