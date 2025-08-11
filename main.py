
from flask import Flask, render_template, request, redirect, session, jsonify, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import sqlite3
import hashlib
import secrets
import datetime
import os
import json
from werkzeug.utils import secure_filename
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configurazione upload file
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'mp4', 'mp3', 'wav'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Crea cartella upload se non esiste
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    """Connessione sicura al database"""
    conn = sqlite3.connect('skaila.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def hash_password(password):
    """Hash sicuro della password"""
    return hashlib.pbkdf2_hex(password.encode('utf-8'), b'skaila_salt', 100000)

def require_auth(f):
    """Decoratore per richiedere autenticazione"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Verifica se il file è consentito"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def can_message(user1_id, user2_id, user1_role, user2_role):
    """Controlla se due utenti possono messaggiare secondo le regole gerarchiche"""
    # Admin può messaggiare con tutti
    if user1_role == 'admin' or user2_role == 'admin':
        return True
    
    # Professore può messaggiare con studenti, professori e dirigenti
    if user1_role == 'professore':
        return user2_role in ['studente', 'professore', 'dirigente']
    
    # Studente può messaggiare con studenti e professori
    if user1_role == 'studente':
        return user2_role in ['studente', 'professore']
    
    # Dirigente può messaggiare con professori e admin
    if user1_role == 'dirigente':
        return user2_role in ['professore', 'admin']
    
    return False

def init_database():
    """Inizializza database completo per messaggistica"""
    conn = get_db_connection()

    # Tabella utenti avanzata
    conn.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            ruolo TEXT NOT NULL CHECK(ruolo IN ('studente', 'professore', 'admin', 'dirigente', 'genitore')),
            classe TEXT,
            scuola TEXT,
            data_nascita DATE,
            telefono TEXT,
            indirizzo TEXT,
            citta TEXT,
            cap TEXT,
            codice_fiscale TEXT UNIQUE,
            avatar_url TEXT DEFAULT '/static/img/default-avatar.png',
            bio TEXT,
            materie_insegnate TEXT,
            data_registrazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_accesso DATETIME,
            email_verificata BOOLEAN DEFAULT 0,
            telefono_verificato BOOLEAN DEFAULT 0,
            attivo BOOLEAN DEFAULT 1,
            primo_accesso BOOLEAN DEFAULT 1,
            impostazioni_privacy TEXT DEFAULT '{}',
            notifiche_email BOOLEAN DEFAULT 1,
            notifiche_push BOOLEAN DEFAULT 1,
            status_online BOOLEAN DEFAULT 0,
            ultima_attivita DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabella conversazioni
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            tipo TEXT NOT NULL CHECK(tipo IN ('privata', 'gruppo_classe', 'gruppo_materia', 'gruppo_custom')),
            classe_id INTEGER,
            materia TEXT,
            descrizione TEXT,
            admin_user_id INTEGER,
            creata_da INTEGER NOT NULL,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultima_attivita DATETIME DEFAULT CURRENT_TIMESTAMP,
            attiva BOOLEAN DEFAULT 1,
            impostazioni TEXT DEFAULT '{}',
            FOREIGN KEY (creata_da) REFERENCES utenti (id),
            FOREIGN KEY (admin_user_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella partecipanti conversazioni
    conn.execute('''
        CREATE TABLE IF NOT EXISTS partecipanti_conversazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversazione_id INTEGER NOT NULL,
            utente_id INTEGER NOT NULL,
            ruolo_conversazione TEXT DEFAULT 'membro' CHECK(ruolo_conversazione IN ('admin', 'moderatore', 'membro')),
            data_aggiunta DATETIME DEFAULT CURRENT_TIMESTAMP,
            aggiunto_da INTEGER,
            attivo BOOLEAN DEFAULT 1,
            notifiche_attive BOOLEAN DEFAULT 1,
            ultima_lettura DATETIME,
            FOREIGN KEY (conversazione_id) REFERENCES conversazioni (id),
            FOREIGN KEY (utente_id) REFERENCES utenti (id),
            FOREIGN KEY (aggiunto_da) REFERENCES utenti (id),
            UNIQUE(conversazione_id, utente_id)
        )
    ''')

    # Tabella messaggi
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messaggi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversazione_id INTEGER NOT NULL,
            utente_id INTEGER NOT NULL,
            contenuto TEXT,
            tipo_messaggio TEXT DEFAULT 'testo' CHECK(tipo_messaggio IN ('testo', 'file', 'immagine', 'audio', 'video', 'sistema')),
            file_url TEXT,
            file_nome TEXT,
            file_size INTEGER,
            risposta_a INTEGER,
            data_invio DATETIME DEFAULT CURRENT_TIMESTAMP,
            modificato BOOLEAN DEFAULT 0,
            data_modifica DATETIME,
            eliminato BOOLEAN DEFAULT 0,
            data_eliminazione DATETIME,
            reazioni TEXT DEFAULT '{}',
            FOREIGN KEY (conversazione_id) REFERENCES conversazioni (id),
            FOREIGN KEY (utente_id) REFERENCES utenti (id),
            FOREIGN KEY (risposta_a) REFERENCES messaggi (id)
        )
    ''')

    # Tabella notifiche
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notifiche (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER NOT NULL,
            conversazione_id INTEGER,
            messaggio_id INTEGER,
            tipo TEXT NOT NULL CHECK(tipo IN ('nuovo_messaggio', 'menzione', 'aggiunta_gruppo', 'rimossa_gruppo')),
            titolo TEXT NOT NULL,
            contenuto TEXT,
            letta BOOLEAN DEFAULT 0,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_lettura DATETIME,
            FOREIGN KEY (utente_id) REFERENCES utenti (id),
            FOREIGN KEY (conversazione_id) REFERENCES conversazioni (id),
            FOREIGN KEY (messaggio_id) REFERENCES messaggi (id)
        )
    ''')

    # Tabella sessioni
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            jwt_token TEXT,
            ip_address TEXT,
            user_agent TEXT,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_scadenza DATETIME,
            attiva BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella classi
    conn.execute('''
        CREATE TABLE IF NOT EXISTS classi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            anno_scolastico TEXT NOT NULL,
            scuola TEXT NOT NULL,
            codice_classe TEXT UNIQUE,
            descrizione TEXT,
            coordinatore_id INTEGER,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            attiva BOOLEAN DEFAULT 1,
            FOREIGN KEY (coordinatore_id) REFERENCES utenti (id)
        )
    ''')

    # Inserimento dati demo se non esistono
    admin_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE ruolo = "admin"').fetchone()[0]
    alessandro_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE email = "alessandro.demo@student.skaila.it"').fetchone()[0]
    
    if admin_exists == 0 or alessandro_exists == 0:
        # Crea admin di default
        admin_password = hash_password('admin123')
        conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, scuola, email_verificata, primo_accesso)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@skaila.it', admin_password, 'Admin', 'SKAILA', 'admin', 'SKAILA Platform', 1, 0))

        # Crea classe demo
        conn.execute('''
            INSERT INTO classi (nome, anno_scolastico, scuola, codice_classe, descrizione)
            VALUES (?, ?, ?, ?, ?)
        ''', ('3A Informatica', '2024-2025', 'IIS Da Vinci', 'DVCI3A24', 'Classe terza informatica'))

        # Crea dirigente demo
        dirigente_password = hash_password('dirigente123')
        conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, scuola, email_verificata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('dirigente.skaila', 'dirigente@skaila.it', dirigente_password, 'Maria', 'Dirigente', 'dirigente', 'IIS Da Vinci', 1))

        # Crea professore demo
        prof_password = hash_password('prof123')
        conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola, materie_insegnate, email_verificata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('prof.rossi', 'prof.rossi@skaila.it', prof_password, 'Mario', 'Rossi', 'professore', '3A', 'IIS Da Vinci', '["Informatica", "Sistemi e Reti"]', 1))

        # Crea altro professore demo
        prof2_password = hash_password('prof2123')
        conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola, materie_insegnate, email_verificata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('prof.verdi', 'prof.verdi@skaila.it', prof2_password, 'Anna', 'Verdi', 'professore', '3A', 'IIS Da Vinci', '["Matematica", "Fisica"]', 1))

        # Crea studenti demo
        stud_password = hash_password('stud123')
        studenti_demo = [
            ('marco.bianchi', 'marco.bianchi@student.skaila.it', 'Marco', 'Bianchi'),
            ('giulia.rossi', 'giulia.rossi@student.skaila.it', 'Giulia', 'Rossi'),
            ('luca.verdi', 'luca.verdi@student.skaila.it', 'Luca', 'Verdi'),
            ('sara.neri', 'sara.neri@student.skaila.it', 'Sara', 'Neri'),
            ('alessandro.demo', 'alessandro.demo@student.skaila.it', 'Alessandro', 'Demo')
        ]
        
        for username, email, nome, cognome in studenti_demo:
            conn.execute('''
                INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola, email_verificata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, stud_password, nome, cognome, 'studente', '3A', 'IIS Da Vinci', 1))

        # Crea conversazione di gruppo classe demo
        conn.execute('''
            INSERT INTO conversazioni (nome, tipo, classe_id, descrizione, creata_da)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Classe 3A Informatica', 'gruppo_classe', 1, 'Chat ufficiale della classe 3A Informatica', 2))

        # Aggiungi partecipanti alla conversazione di classe
        users = conn.execute('SELECT id FROM utenti WHERE classe = "3A" OR ruolo IN ("admin", "dirigente")').fetchall()
        for user in users:
            conn.execute('''
                INSERT INTO partecipanti_conversazioni (conversazione_id, utente_id, aggiunto_da)
                VALUES (?, ?, ?)
            ''', (1, user[0], 2))

        # Crea conversazione professori
        conn.execute('''
            INSERT INTO conversazioni (nome, tipo, descrizione, creata_da)
            VALUES (?, ?, ?, ?)
        ''', ('Staff Docenti', 'gruppo_custom', 'Chat riservata ai docenti della scuola', 2))

        # Aggiungi professori alla conversazione staff
        professori = conn.execute('SELECT id FROM utenti WHERE ruolo IN ("professore", "dirigente", "admin")').fetchall()
        for prof in professori:
            conn.execute('''
                INSERT INTO partecipanti_conversazioni (conversazione_id, utente_id, aggiunto_da)
                VALUES (?, ?, ?)
            ''', (2, prof[0], 2))

        # Messaggi demo
        messaggi_demo = [
            (1, 2, "👋 Benvenuti nella chat della classe 3A! Qui potete comunicare per progetti, compiti e tutto quello che riguarda la scuola.", 'sistema'),
            (1, 3, "Buongiorno a tutti! Ricordo che domani abbiamo il compito di informatica. Studiate bene gli algoritmi!", 'testo'),
            (1, 4, "Ciao ragazzi! Per chi ha dubbi sulla verifica di matematica, sono disponibile oggi pomeriggio per ripetizioni.", 'testo'),
            (1, 5, "Grazie prof Rossi! Io avrei qualche dubbio sugli array bidimensionali 🤔", 'testo'),
            (2, 1, "🏫 Benvenuti nella chat dello Staff Docenti. Qui potete coordinarvi per le attività didattiche.", 'sistema'),
            (2, 2, "Colleghi, ricordo che domani abbiamo il consiglio di classe alle 16:00", 'testo'),
        ]

        for conv_id, user_id, contenuto, tipo in messaggi_demo:
            conn.execute('''
                INSERT INTO messaggi (conversazione_id, utente_id, contenuto, tipo_messaggio)
                VALUES (?, ?, ?, ?)
            ''', (conv_id, user_id, contenuto, tipo))

    conn.commit()
    conn.close()
    print("✅ Database completo per messaggistica inizializzato!")

# ROUTES PRINCIPALI
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email e password sono obbligatorie')
            return render_template('login.html', error='Email e password sono obbligatorie')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM utenti WHERE email = ? AND attivo = 1', (email,)).fetchone()
        
        print(f"🔍 Debug Login - Email: {email}")
        print(f"🔍 Debug Login - User found: {'Yes' if user else 'No'}")
        
        if user:
            input_hash = hash_password(password)
            stored_hash = user['password_hash']
            print(f"🔍 Debug Login - Password match: {input_hash == stored_hash}")
            
            if stored_hash == input_hash:
                # Login riuscito
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['nome'] = user['nome']
                session['cognome'] = user['cognome']
                session['ruolo'] = user['ruolo']
                session['email'] = user['email']
                session['classe'] = user['classe']
                
                # Aggiorna ultimo accesso e status online
                conn.execute('''
                    UPDATE utenti 
                    SET ultimo_accesso = CURRENT_TIMESTAMP, status_online = 1, primo_accesso = 0
                    WHERE id = ?
                ''', (user['id'],))
                conn.commit()
                conn.close()
                
                print(f"✅ Login successful for: {user['nome']} {user['cognome']}")
                return redirect('/chat')
        
        conn.close()
        print("❌ Login failed - Invalid credentials")
        return render_template('login.html', error='Email o password non corretti. Controlla di aver inserito: alessandro.demo@student.skaila.it')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Raccolta dati dal form
            nome = request.form.get('nome', '').strip()
            cognome = request.form.get('cognome', '').strip()
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            ruolo = request.form.get('ruolo', 'studente')
            classe = request.form.get('classe', '').strip()
            
            # Validazioni base
            if not all([nome, cognome, email, password]):
                return render_template('register.html', error='Tutti i campi sono obbligatori')
            
            if len(password) < 6:
                return render_template('register.html', error='La password deve essere di almeno 6 caratteri')
            
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return render_template('register.html', error='Formato email non valido')
            
            # Genera username automaticamente
            username = f"{nome.lower()}.{cognome.lower()}"
            
            conn = get_db_connection()
            
            # Controlla se email già esiste
            existing = conn.execute('SELECT id FROM utenti WHERE email = ?', (email,)).fetchone()
            if existing:
                conn.close()
                return render_template('register.html', error='Email già registrata')
            
            # Controlla se username già esiste e genera alternativa
            counter = 1
            original_username = username
            while conn.execute('SELECT id FROM utenti WHERE username = ?', (username,)).fetchone():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Crea nuovo utente
            password_hash = hash_password(password)
            conn.execute('''
                INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, nome, cognome, ruolo, classe, 'IIS Da Vinci'))
            
            user_id = conn.lastrowid
            
            # Se è uno studente e c'è una classe, aggiungilo alla conversazione di classe
            if ruolo == 'studente' and classe:
                conv_classe = conn.execute('''
                    SELECT c.id FROM conversazioni c
                    JOIN classi cl ON c.classe_id = cl.id 
                    WHERE cl.nome LIKE ? AND c.tipo = 'gruppo_classe'
                ''', (f'%{classe}%',)).fetchone()
                
                if conv_classe:
                    conn.execute('''
                        INSERT INTO partecipanti_conversazioni (conversazione_id, utente_id, aggiunto_da)
                        VALUES (?, ?, ?)
                    ''', (conv_classe[0], user_id, 1))
            
            # Se è un professore, aggiungilo alla chat staff docenti
            if ruolo == 'professore':
                conv_staff = conn.execute('''
                    SELECT id FROM conversazioni 
                    WHERE nome = 'Staff Docenti' AND tipo = 'gruppo_custom'
                ''').fetchone()
                
                if conv_staff:
                    conn.execute('''
                        INSERT INTO partecipanti_conversazioni (conversazione_id, utente_id, aggiunto_da)
                        VALUES (?, ?, ?)
                    ''', (conv_staff[0], user_id, 1))
            
            conn.commit()
            conn.close()
            
            flash('Registrazione completata! Ora puoi effettuare il login.')
            return redirect('/login')
            
        except Exception as e:
            return render_template('register.html', error=f'Errore durante la registrazione: {str(e)}')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        # Imposta utente offline
        conn = get_db_connection()
        conn.execute('UPDATE utenti SET status_online = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    session.clear()
    return redirect('/')

@app.route('/chat')
@require_auth
def chat():
    return render_template('chat.html')

# API ENDPOINTS
@app.route('/api/conversations')
@require_auth
def api_conversations():
    """Ottieni tutte le conversazioni dell'utente"""
    conn = get_db_connection()
    user_id = session['user_id']
    
    conversations = conn.execute('''
        SELECT DISTINCT c.id, c.nome, c.tipo, c.ultima_attivita, c.descrizione,
               COUNT(DISTINCT pc2.utente_id) as partecipanti_count,
               MAX(m.data_invio) as ultimo_messaggio_data,
               (SELECT contenuto FROM messaggi WHERE conversazione_id = c.id ORDER BY data_invio DESC LIMIT 1) as ultimo_messaggio,
               (SELECT nome || ' ' || cognome FROM utenti WHERE id = 
                (SELECT utente_id FROM messaggi WHERE conversazione_id = c.id ORDER BY data_invio DESC LIMIT 1)) as ultimo_mittente,
               COALESCE(pc.ultima_lettura, '1970-01-01') as ultima_lettura,
               COUNT(CASE WHEN m.data_invio > COALESCE(pc.ultima_lettura, '1970-01-01') AND m.utente_id != ? THEN 1 END) as messaggi_non_letti
        FROM conversazioni c
        JOIN partecipanti_conversazioni pc ON c.id = pc.conversazione_id
        LEFT JOIN partecipanti_conversazioni pc2 ON c.id = pc2.conversazione_id AND pc2.attivo = 1
        LEFT JOIN messaggi m ON c.id = m.conversazione_id AND m.eliminato = 0
        WHERE pc.utente_id = ? AND pc.attivo = 1 AND c.attiva = 1
        GROUP BY c.id, c.nome, c.tipo, c.ultima_attivita, c.descrizione, pc.ultima_lettura
        ORDER BY COALESCE(MAX(m.data_invio), c.data_creazione) DESC
    ''', (user_id, user_id)).fetchall()
    
    conn.close()
    return jsonify([dict(conv) for conv in conversations])

@app.route('/api/messages/<int:conversation_id>')
@require_auth
def api_messages(conversation_id):
    """Ottieni messaggi di una conversazione"""
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Verifica che l'utente possa accedere alla conversazione
    access = conn.execute('''
        SELECT 1 FROM partecipanti_conversazioni 
        WHERE conversazione_id = ? AND utente_id = ? AND attivo = 1
    ''', (conversation_id, user_id)).fetchone()
    
    if not access:
        conn.close()
        return jsonify({'error': 'Accesso negato'}), 403
    
    # Ottieni messaggi
    messages = conn.execute('''
        SELECT m.*, u.nome, u.cognome, u.username, u.avatar_url,
               rm.contenuto as risposta_contenuto,
               ru.nome as risposta_nome, ru.cognome as risposta_cognome
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        LEFT JOIN messaggi rm ON m.risposta_a = rm.id
        LEFT JOIN utenti ru ON rm.utente_id = ru.id
        WHERE m.conversazione_id = ? AND m.eliminato = 0
        ORDER BY m.data_invio ASC
    ''', (conversation_id,)).fetchall()
    
    # Aggiorna ultima lettura
    conn.execute('''
        UPDATE partecipanti_conversazioni 
        SET ultima_lettura = CURRENT_TIMESTAMP 
        WHERE conversazione_id = ? AND utente_id = ?
    ''', (conversation_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify([dict(msg) for msg in messages])

@app.route('/api/users/search')
@require_auth
def api_search_users():
    """Cerca utenti per iniziare nuove conversazioni"""
    query = request.args.get('q', '').strip()
    user_id = session['user_id']
    user_role = session['ruolo']
    
    if len(query) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    
    # Cerca utenti escludendo se stesso
    users = conn.execute('''
        SELECT id, nome, cognome, username, email, ruolo, classe, avatar_url, status_online
        FROM utenti 
        WHERE (nome LIKE ? OR cognome LIKE ? OR username LIKE ? OR email LIKE ?) 
              AND id != ? AND attivo = 1
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', user_id)).fetchall()
    
    # Filtra utenti secondo le regole di messaggistica
    filtered_users = []
    for user in users:
        if can_message(user_id, user['id'], user_role, user['ruolo']):
            filtered_users.append(dict(user))
    
    conn.close()
    return jsonify(filtered_users)

@app.route('/api/conversation/create', methods=['POST'])
@require_auth
def api_create_conversation():
    """Crea una nuova conversazione"""
    data = request.get_json()
    user_id = session['user_id']
    
    tipo = data.get('tipo', 'privata')
    nome = data.get('nome', '')
    partecipanti_ids = data.get('partecipanti', [])
    descrizione = data.get('descrizione', '')
    
    if tipo == 'privata' and len(partecipanti_ids) != 1:
        return jsonify({'error': 'Chat privata deve avere esattamente 2 partecipanti'}), 400
    
    conn = get_db_connection()
    
    # Per chat private, controlla se esiste già
    if tipo == 'privata':
        other_user_id = partecipanti_ids[0]
        existing = conn.execute('''
            SELECT c.id FROM conversazioni c
            JOIN partecipanti_conversazioni pc1 ON c.id = pc1.conversazione_id
            JOIN partecipanti_conversazioni pc2 ON c.id = pc2.conversazione_id
            WHERE c.tipo = 'privata' AND pc1.utente_id = ? AND pc2.utente_id = ?
        ''', (user_id, other_user_id)).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'conversation_id': existing[0]})
    
    # Crea conversazione
    if tipo == 'privata':
        # Nome automatico per chat private
        other_user = conn.execute('SELECT nome, cognome FROM utenti WHERE id = ?', (partecipanti_ids[0],)).fetchone()
        nome = f"{other_user['nome']} {other_user['cognome']}"
    
    cursor = conn.execute('''
        INSERT INTO conversazioni (nome, tipo, descrizione, creata_da)
        VALUES (?, ?, ?, ?)
    ''', (nome, tipo, descrizione, user_id))
    
    conversation_id = cursor.lastrowid
    
    # Aggiungi creatore
    conn.execute('''
        INSERT INTO partecipanti_conversazioni (conversazione_id, utente_id, ruolo_conversazione, aggiunto_da)
        VALUES (?, ?, ?, ?)
    ''', (conversation_id, user_id, 'admin' if tipo != 'privata' else 'membro', user_id))
    
    # Aggiungi altri partecipanti
    for partecipante_id in partecipanti_ids:
        conn.execute('''
            INSERT INTO partecipanti_conversazioni (conversazione_id, utente_id, aggiunto_da)
            VALUES (?, ?, ?)
        ''', (conversation_id, partecipante_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'conversation_id': conversation_id})

@app.route('/api/upload', methods=['POST'])
@require_auth
def api_upload_file():
    """Upload file per messaggi"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo file non consentito'}), 400
    
    # Genera nome file sicuro
    filename = secure_filename(file.filename)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
    unique_filename = f"{timestamp}{filename}"
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    file_url = f"/static/uploads/{unique_filename}"
    file_size = os.path.getsize(file_path)
    
    return jsonify({
        'file_url': file_url,
        'file_name': filename,
        'file_size': file_size
    })

# WEBSOCKET EVENTS
@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        return False
    
    user_id = session['user_id']
    join_room(f'user_{user_id}')
    
    # Imposta utente online
    conn = get_db_connection()
    conn.execute('UPDATE utenti SET status_online = 1, ultima_attivita = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    emit('connected', {'message': 'Connesso al sistema di messaggistica SKAILA'})

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Imposta utente offline
        conn = get_db_connection()
        conn.execute('UPDATE utenti SET status_online = 0, ultima_attivita = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

@socketio.on('join_conversation')
def handle_join_conversation(data):
    if 'user_id' not in session:
        return
    
    conversation_id = data['conversation_id']
    user_id = session['user_id']
    
    # Verifica accesso alla conversazione
    conn = get_db_connection()
    access = conn.execute('''
        SELECT 1 FROM partecipanti_conversazioni 
        WHERE conversazione_id = ? AND utente_id = ? AND attivo = 1
    ''', (conversation_id, user_id)).fetchone()
    
    if access:
        join_room(f'conv_{conversation_id}')
        emit('joined_conversation', {'conversation_id': conversation_id})
    
    conn.close()

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    
    user_id = session['user_id']
    conversation_id = data['conversation_id']
    contenuto = data.get('contenuto', '').strip()
    tipo_messaggio = data.get('tipo', 'testo')
    file_url = data.get('file_url')
    file_nome = data.get('file_name')
    file_size = data.get('file_size')
    risposta_a = data.get('risposta_a')
    
    if not contenuto and not file_url:
        return
    
    conn = get_db_connection()
    
    # Verifica accesso
    access = conn.execute('''
        SELECT 1 FROM partecipanti_conversazioni 
        WHERE conversazione_id = ? AND utente_id = ? AND attivo = 1
    ''', (conversation_id, user_id)).fetchone()
    
    if not access:
        conn.close()
        return
    
    # Inserisci messaggio
    cursor = conn.execute('''
        INSERT INTO messaggi (conversazione_id, utente_id, contenuto, tipo_messaggio, file_url, file_nome, file_size, risposta_a)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (conversation_id, user_id, contenuto, tipo_messaggio, file_url, file_nome, file_size, risposta_a))
    
    message_id = cursor.lastrowid
    
    # Aggiorna ultima attività conversazione
    conn.execute('UPDATE conversazioni SET ultima_attivita = CURRENT_TIMESTAMP WHERE id = ?', (conversation_id,))
    
    # Ottieni info messaggio completo
    message = conn.execute('''
        SELECT m.*, u.nome, u.cognome, u.username, u.avatar_url
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        WHERE m.id = ?
    ''', (message_id,)).fetchone()
    
    # Ottieni partecipanti per notifiche
    partecipanti = conn.execute('''
        SELECT utente_id FROM partecipanti_conversazioni 
        WHERE conversazione_id = ? AND attivo = 1 AND utente_id != ?
    ''', (conversation_id, user_id)).fetchall()
    
    # Crea notifiche
    for partecipante in partecipanti:
        conn.execute('''
            INSERT INTO notifiche (utente_id, conversazione_id, messaggio_id, tipo, titolo, contenuto)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (partecipante[0], conversation_id, message_id, 'nuovo_messaggio', 
              f'Nuovo messaggio da {session["nome"]}', contenuto[:100]))
    
    conn.commit()
    conn.close()
    
    # Invia messaggio a tutti i partecipanti della conversazione
    socketio.emit('new_message', dict(message), room=f'conv_{conversation_id}')

@socketio.on('typing_start')
def handle_typing_start(data):
    if 'user_id' not in session:
        return
    
    conversation_id = data['conversation_id']
    user_name = session['nome']
    
    socketio.emit('user_typing', {
        'conversation_id': conversation_id,
        'user_name': user_name,
        'typing': True
    }, room=f'conv_{conversation_id}', include_self=False)

@socketio.on('typing_stop')
def handle_typing_stop(data):
    if 'user_id' not in session:
        return
    
    conversation_id = data['conversation_id']
    user_name = session['nome']
    
    socketio.emit('user_typing', {
        'conversation_id': conversation_id,
        'user_name': user_name,
        'typing': False
    }, room=f'conv_{conversation_id}', include_self=False)

if __name__ == '__main__':
    init_database()
    print("🚀 SKAILA Sistema Messaggistica Completo!")
    print("📍 http://localhost:5000")
    print("\n👤 Account Demo:")
    print("🔧 Admin: admin@skaila.it / admin123")
    print("👨‍🏫 Professore: prof.rossi@skaila.it / prof123")
    print("👨‍🏫 Professoressa: prof.verdi@skaila.it / prof2123") 
    print("🏫 Dirigente: dirigente@skaila.it / dirigente123")
    print("🎓 Studenti:")
    print("   - marco.bianchi@student.skaila.it / stud123")
    print("   - giulia.rossi@student.skaila.it / stud123")
    print("   - luca.verdi@student.skaila.it / stud123")
    print("   - sara.neri@student.skaila.it / stud123")
    print("   - alessandro.demo@student.skaila.it / stud123")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
