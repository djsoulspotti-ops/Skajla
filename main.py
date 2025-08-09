from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import os
import re
import jwt
from functools import wraps

app = Flask(__name__)
app.secret_key = 'skaila_super_secret_key_2024_production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurazione database
DATABASE = 'skaila.db'
JWT_SECRET = 'skaila_jwt_secret_key_2024'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inizializza database con schema completo"""
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
            ruolo TEXT NOT NULL CHECK(ruolo IN ('studente', 'professore', 'admin', 'genitore')),
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
            materie_insegnate TEXT, -- JSON per professori
            data_registrazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_accesso DATETIME,
            email_verificata BOOLEAN DEFAULT 0,
            telefono_verificato BOOLEAN DEFAULT 0,
            attivo BOOLEAN DEFAULT 1,
            primo_accesso BOOLEAN DEFAULT 1,
            impostazioni_privacy TEXT DEFAULT '{}', -- JSON
            notifiche_email BOOLEAN DEFAULT 1,
            notifiche_push BOOLEAN DEFAULT 1
        )
    ''')

    # Tabella classi
    conn.execute('''
        CREATE TABLE IF NOT EXISTS classi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            anno_scolastico TEXT NOT NULL,
            scuola TEXT NOT NULL,
            professore_coordinatore_id INTEGER,
            descrizione TEXT,
            codice_classe TEXT UNIQUE NOT NULL,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            attiva BOOLEAN DEFAULT 1,
            FOREIGN KEY (professore_coordinatore_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella iscrizioni classi (many-to-many)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS iscrizioni_classi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER,
            classe_id INTEGER,
            ruolo_classe TEXT DEFAULT 'studente',
            data_iscrizione DATETIME DEFAULT CURRENT_TIMESTAMP,
            attiva BOOLEAN DEFAULT 1,
            FOREIGN KEY (utente_id) REFERENCES utenti (id),
            FOREIGN KEY (classe_id) REFERENCES classi (id),
            UNIQUE(utente_id, classe_id)
        )
    ''')

    # Tabella sessioni sicure
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

    # Tabella tentativi di login (sicurezza)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tentativi_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            ip_address TEXT,
            successo BOOLEAN,
            data_tentativo DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT
        )
    ''')

    # Tabella tokens di verifica
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tokens_verifica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            tipo TEXT CHECK(tipo IN ('email', 'password_reset', 'phone')),
            scadenza DATETIME,
            utilizzato BOOLEAN DEFAULT 0,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES utenti (id)
        )
    ''')

    # Inserimento dati demo se non esistono
    admin_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE ruolo = "admin"').fetchone()[0]
    if admin_exists == 0:
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

        # Crea professore demo
        prof_password = hash_password('prof123')
        conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola, materie_insegnate, email_verificata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('prof.rossi', 'prof.rossi@skaila.it', prof_password, 'Mario', 'Rossi', 'professore', '3A', 'IIS Da Vinci', '["Informatica", "Sistemi e Reti"]', 1))

        # Crea studente demo
        stud_password = hash_password('stud123')
        conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe, scuola, email_verificata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('marco.bianchi', 'marco.bianchi@student.skaila.it', stud_password, 'Marco', 'Bianchi', 'studente', '3A', 'IIS Da Vinci', 1))

    conn.commit()
    conn.close()
    print("✅ Database avanzato inizializzato!")

def hash_password(password):
    """Hash sicuro delle password con salt"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                        password.encode('utf-8'), 
                                        salt.encode('utf-8'), 
                                        100000)
    return salt + password_hash.hex()

def verify_password(password, stored_hash):
    """Verifica password"""
    salt = stored_hash[:64]
    stored_password = stored_hash[64:]
    password_hash = hashlib.pbkdf2_hmac('sha256',
                                        password.encode('utf-8'),
                                        salt.encode('utf-8'),
                                        100000)
    return password_hash.hex() == stored_password

def validate_email(email):
    """Validazione email avanzata"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validazione password sicura"""
    if len(password) < 8:
        return False, "Password deve essere almeno 8 caratteri"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password deve contenere almeno una lettera"
    if not re.search(r'\d', password):
        return False, "Password deve contenere almeno un numero"
    return True, "Password valida"

def generate_jwt_token(user_id, username, ruolo):
    """Genera JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'ruolo': ruolo,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token):
    """Verifica JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator per route che richiedono autenticazione"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def require_role(allowed_roles):
    """Decorator per controllo ruoli"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('ruolo') not in allowed_roles:
                flash('Non autorizzato per questa operazione', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def log_login_attempt(email, ip_address, user_agent, success):
    """Log tentativi di login per sicurezza"""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tentativi_login (email, ip_address, successo, user_agent)
        VALUES (?, ?, ?, ?)
    ''', (email, ip_address, user_agent, success))
    conn.commit()
    conn.close()

def check_login_attempts(email, ip_address):
    """Controllo rate limiting login"""
    conn = get_db_connection()
    # Controlla tentativi falliti ultimi 15 minuti
    attempts = conn.execute('''
        SELECT COUNT(*) FROM tentativi_login 
        WHERE (email = ? OR ip_address = ?) 
        AND successo = 0 
        AND data_tentativo > datetime('now', '-15 minutes')
    ''', (email, ip_address)).fetchone()[0]
    conn.close()

    return attempts < 5  # Max 5 tentativi in 15 minuti

# ==================== ROUTES AUTENTICAZIONE ====================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/registrazione')
def registrazione_page():
    return render_template('registrazione.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@require_auth
def dashboard():
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM utenti WHERE id = ?', (session['user_id'],)
    ).fetchone()

    # Informazioni specifiche per ruolo
    if user['ruolo'] == 'studente':
        # Classi dello studente
        classi = conn.execute('''
            SELECT c.* FROM classi c
            JOIN iscrizioni_classi ic ON c.id = ic.classe_id
            WHERE ic.utente_id = ? AND ic.attiva = 1
        ''', (user['id'],)).fetchall()
    elif user['ruolo'] == 'professore':
        # Classi del professore
        classi = conn.execute('''
            SELECT c.* FROM classi c
            JOIN iscrizioni_classi ic ON c.id = ic.classe_id
            WHERE ic.utente_id = ? AND ic.attiva = 1
        ''', (user['id'],)).fetchall()
    else:
        classi = []

    conn.close()

    return render_template('dashboard.html', user=dict(user), classi=[dict(c) for c in classi])

# ==================== API ROUTES ====================

@app.route('/api/registrazione', methods=['POST'])
def api_registrazione():
    try:
        data = request.get_json()

        # Validazione campi obbligatori
        required_fields = ['username', 'email', 'password', 'nome', 'cognome', 'ruolo']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} obbligatorio'}), 400

        # Validazione email
        if not validate_email(data['email']):
            return jsonify({'error': 'Email non valida'}), 400

        # Validazione password
        password_valid, password_msg = validate_password(data['password'])
        if not password_valid:
            return jsonify({'error': password_msg}), 400

        # Validazione ruolo
        if data['ruolo'] not in ['studente', 'professore', 'genitore']:
            return jsonify({'error': 'Ruolo non valido'}), 400

        conn = get_db_connection()

        # Controllo duplicati
        existing = conn.execute(
            'SELECT id FROM utenti WHERE username = ? OR email = ?',
            (data['username'], data['email'])
        ).fetchone()

        if existing:
            return jsonify({'error': 'Username o email già registrati'}), 400

        # Hash password
        password_hash = hash_password(data['password'])

        # Inserimento utente
        cursor = conn.execute('''
            INSERT INTO utenti (
                username, email, password_hash, nome, cognome, ruolo, 
                classe, scuola, data_nascita, telefono, codice_fiscale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'], data['email'], password_hash,
            data['nome'], data['cognome'], data['ruolo'],
            data.get('classe', ''), data.get('scuola', ''),
            data.get('data_nascita'), data.get('telefono'),
            data.get('codice_fiscale')
        ))

        user_id = cursor.lastrowid

        # Se è uno studente, iscrivilo alla classe se specificata
        if data['ruolo'] == 'studente' and data.get('codice_classe'):
            classe = conn.execute(
                'SELECT id FROM classi WHERE codice_classe = ?',
                (data['codice_classe'],)
            ).fetchone()

            if classe:
                conn.execute('''
                    INSERT INTO iscrizioni_classi (utente_id, classe_id, ruolo_classe)
                    VALUES (?, ?, ?)
                ''', (user_id, classe['id'], 'studente'))

        conn.commit()
        conn.close()

        # Log successful registration
        log_login_attempt(data['email'], request.remote_addr, request.headers.get('User-Agent'), True)

        return jsonify({
            'success': True,
            'message': 'Registrazione completata con successo!',
            'user_id': user_id
        }), 201

    except Exception as e:
        return jsonify({'error': f'Errore server: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email e password obbligatori'}), 400

        # Rate limiting
        if not check_login_attempts(email, request.remote_addr):
            return jsonify({'error': 'Troppi tentativi di login. Riprova tra 15 minuti'}), 429

        conn = get_db_connection()

        # Trova utente (supporta login con email o username)
        user = conn.execute('''
            SELECT * FROM utenti 
            WHERE (email = ? OR username = ?) AND attivo = 1
        ''', (email, email)).fetchone()

        if not user or not verify_password(password, user['password_hash']):
            log_login_attempt(email, request.remote_addr, request.headers.get('User-Agent'), False)
            return jsonify({'error': 'Credenziali non valide'}), 401

        # Aggiorna ultimo accesso
        conn.execute(
            'UPDATE utenti SET ultimo_accesso = CURRENT_TIMESTAMP WHERE id = ?',
            (user['id'],)
        )

        # Genera JWT token
        jwt_token = generate_jwt_token(user['id'], user['username'], user['ruolo'])

        # Salva sessione nel database
        session_token = secrets.token_urlsafe(32)
        conn.execute('''
            INSERT INTO sessioni (user_id, token, jwt_token, ip_address, user_agent, data_scadenza)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user['id'], session_token, jwt_token,
            request.remote_addr, request.headers.get('User-Agent'),
            datetime.now() + timedelta(days=7)
        ))

        conn.commit()
        conn.close()

        # Crea sessione Flask
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['ruolo'] = user['ruolo']
        session['nome_completo'] = f"{user['nome']} {user['cognome']}"
        session['session_token'] = session_token

        # Log successful login
        log_login_attempt(email, request.remote_addr, request.headers.get('User-Agent'), True)

        return jsonify({
            'success': True,
            'message': 'Login effettuato con successo!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'ruolo': user['ruolo'],
                'primo_accesso': bool(user['primo_accesso'])
            },
            'jwt_token': jwt_token
        })

    except Exception as e:
        return jsonify({'error': f'Errore server: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    if 'session_token' in session:
        conn = get_db_connection()
        conn.execute(
            'UPDATE sessioni SET attiva = 0 WHERE token = ?',
            (session['session_token'],)
        )
        conn.commit()
        conn.close()

    session.clear()
    return jsonify({'success': True, 'message': 'Logout effettuato'})

@app.route('/api/profilo')
@require_auth
def api_profilo():
    conn = get_db_connection()
    user = conn.execute('''
        SELECT id, username, email, nome, cognome, ruolo, classe, scuola, 
               data_nascita, telefono, bio, avatar_url, data_registrazione,
               ultimo_accesso, email_verificata, notifiche_email, notifiche_push
        FROM utenti WHERE id = ?
    ''', (session['user_id'],)).fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Utente non trovato'}), 404

    return jsonify(dict(user))

@app.route('/api/aggiorna-profilo', methods=['PUT'])
@require_auth
def api_aggiorna_profilo():
    try:
        data = request.get_json()

        # Campi modificabili
        allowed_fields = ['nome', 'cognome', 'telefono', 'bio', 'classe', 'scuola', 'data_nascita']
        updates = {}

        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]

        if not updates:
            return jsonify({'error': 'Nessun campo da aggiornare'}), 400

        # Costruisci query dinamica
        set_clause = ', '.join([f'{field} = ?' for field in updates.keys()])
        values = list(updates.values()) + [session['user_id']]

        conn = get_db_connection()
        conn.execute(f'UPDATE utenti SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Profilo aggiornato'})

    except Exception as e:
        return jsonify({'error': f'Errore: {str(e)}'}), 500

@app.route('/api/cambia-password', methods=['POST'])
@require_auth
def api_cambia_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({'error': 'Password attuale e nuova obbligatorie'}), 400

        # Validazione nuova password
        password_valid, password_msg = validate_password(new_password)
        if not password_valid:
            return jsonify({'error': password_msg}), 400

        conn = get_db_connection()
        user = conn.execute(
            'SELECT password_hash FROM utenti WHERE id = ?',
            (session['user_id'],)
        ).fetchone()

        if not verify_password(current_password, user['password_hash']):
            return jsonify({'error': 'Password attuale non corretta'}), 400

        # Aggiorna password
        new_hash = hash_password(new_password)
        conn.execute(
            'UPDATE utenti SET password_hash = ?, primo_accesso = 0 WHERE id = ?',
            (new_hash, session['user_id'])
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Password cambiata con successo'})

    except Exception as e:
        return jsonify({'error': f'Errore: {str(e)}'}), 500

@app.route('/api/classi')
@require_auth
def api_classi():
    conn = get_db_connection()

    if session['ruolo'] == 'admin':
        # Admin vede tutte le classi
        classi = conn.execute('SELECT * FROM classi WHERE attiva = 1').fetchall()
    else:
        # Altri vedono solo le proprie classi
        classi = conn.execute('''
            SELECT c.* FROM classi c
            JOIN iscrizioni_classi ic ON c.id = ic.classe_id
            WHERE ic.utente_id = ? AND ic.attiva = 1 AND c.attiva = 1
        ''', (session['user_id'],)).fetchall()

    conn.close()
    return jsonify([dict(classe) for classe in classi])

if __name__ == '__main__':
    init_database()
    print("🚀 SKAILA Sistema Autenticazione Completo!")
    print("📍 http://localhost:5000")
    print("\n👤 Account Demo:")
    print("🔧 Admin: admin@skaila.it / admin123")
    print("👨‍🏫 Professore: prof.rossi@skaila.it / prof123") 
    print("🎓 Studente: marco.bianchi@student.skaila.it / stud123")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
