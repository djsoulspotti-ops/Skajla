from flask import Flask, request, jsonify, session, render_template
from flask_socketio import SocketIO
import sqlite3
import hashlib
import secrets
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'skaila_super_secret_key_2024'  # Cambia questa in produzione!
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurazione database
DATABASE = 'skaila.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inizializza database con tabelle necessarie"""
    conn = get_db_connection()

    # Tabella utenti migliorata
    conn.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            ruolo TEXT DEFAULT 'studente',
            classe TEXT,
            data_registrazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_accesso DATETIME,
            attivo BOOLEAN DEFAULT 1
        )
    ''')

    # Tabella sessioni per sicurezza
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_scadenza DATETIME,
            FOREIGN KEY (user_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella messaggi per chat
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messaggi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mittente_id INTEGER,
            destinatario_id INTEGER,
            contenuto TEXT NOT NULL,
            data_invio DATETIME DEFAULT CURRENT_TIMESTAMP,
            letto BOOLEAN DEFAULT 0,
            tipo TEXT DEFAULT 'testo',
            FOREIGN KEY (mittente_id) REFERENCES utenti (id),
            FOREIGN KEY (destinatario_id) REFERENCES utenti (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database inizializzato!")

def hash_password(password):
    """Hash sicuro delle password"""
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

# ==================== ROUTES API ====================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/registrazione', methods=['POST'])
def registrazione():
    try:
        data = request.get_json()

        # Validazione input
        required_fields = ['username', 'email', 'password', 'nome', 'cognome']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} obbligatorio'}), 400

        # Controllo lunghezza password
        if len(data['password']) < 6:
            return jsonify({'error': 'Password deve essere almeno 6 caratteri'}), 400

        conn = get_db_connection()

        # Controllo se utente già esistente
        existing = conn.execute(
            'SELECT id FROM utenti WHERE username = ? OR email = ?',
            (data['username'], data['email'])
        ).fetchone()

        if existing:
            return jsonify({'error': 'Username o email già registrati'}), 400

        # Hash password
        password_hash = hash_password(data['password'])

        # Inserimento nuovo utente
        cursor = conn.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, classe)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'],
            data['email'], 
            password_hash,
            data['nome'],
            data['cognome'],
            data.get('ruolo', 'studente'),
            data.get('classe', '')
        ))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Registrazione completata!',
            'user_id': user_id
        }), 201

    except Exception as e:
        return jsonify({'error': f'Errore server: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username e password obbligatori'}), 400

        conn = get_db_connection()

        # Trova utente
        user = conn.execute(
            'SELECT * FROM utenti WHERE username = ? AND attivo = 1',
            (username,)
        ).fetchone()

        if not user or not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Credenziali non valide'}), 401

        # Aggiorna ultimo accesso
        conn.execute(
            'UPDATE utenti SET ultimo_accesso = CURRENT_TIMESTAMP WHERE id = ?',
            (user['id'],)
        )
        conn.commit()
        conn.close()

        # Crea sessione
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['ruolo'] = user['ruolo']

        return jsonify({
            'success': True,
            'message': 'Login effettuato!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'ruolo': user['ruolo'],
                'classe': user['classe']
            }
        })

    except Exception as e:
        return jsonify({'error': f'Errore server: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout effettuato'})

@app.route('/api/profilo')
def profilo():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, email, nome, cognome, ruolo, classe, data_registrazione FROM utenti WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Utente non trovato'}), 404

    return jsonify(dict(user))

@app.route('/api/utenti')
def lista_utenti():
    """Lista tutti gli utenti - solo per admin/professori"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    if session.get('ruolo') not in ['admin', 'professore']:
        return jsonify({'error': 'Non autorizzato'}), 403

    conn = get_db_connection()
    utenti = conn.execute(
        'SELECT id, username, nome, cognome, ruolo, classe FROM utenti WHERE attivo = 1 ORDER BY cognome, nome'
    ).fetchall()
    conn.close()

    return jsonify([dict(user) for user in utenti])

# ==================== SOCKET.IO per CHAT ====================

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        print(f"✅ {session['username']} si è connesso alla chat")
    else:
        print("❌ Tentativo connessione non autenticata")

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        print(f"🔌 {session['username']} si è disconnesso")

@socketio.on('nuovo_messaggio')
def handle_message(data):
    if 'user_id' not in session:
        return

    # Salva messaggio nel database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO messaggi (mittente_id, destinatario_id, contenuto)
        VALUES (?, ?, ?)
    ''', (session['user_id'], data.get('destinatario_id'), data.get('contenuto')))
    conn.commit()
    conn.close()

    # Invia a tutti (per ora)
    socketio.emit('messaggio_ricevuto', {
        'mittente': session['username'],
        'contenuto': data['contenuto'],
        'timestamp': datetime.now().strftime('%H:%M')
    })

if __name__ == '__main__':
    init_database()
    print("🚀 SKAILA Server avviato!")
    print("📍 http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

