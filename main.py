
import sqlite3
import hashlib
from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import openai
from ai_chatbot import AIChestBot

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skaila_secret_key_super_secure_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configurazione sessioni permanenti
app.permanent_session_lifetime = timedelta(days=30)

socketio = SocketIO(app, cors_allowed_origins="*")

# Inizializza il chatbot AI
ai_bot = AIChestBot()

# Utility per password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database connection
def get_db_connection():
    conn = sqlite3.connect('skaila.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inizializzazione database
def init_db():
    conn = get_db_connection()
    
    # Tabella utenti
    conn.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            classe TEXT,
            ruolo TEXT DEFAULT 'studente',
            attivo BOOLEAN DEFAULT 1,
            primo_accesso BOOLEAN DEFAULT 1,
            ultimo_accesso TIMESTAMP,
            status_online BOOLEAN DEFAULT 0,
            avatar TEXT DEFAULT 'default.jpg',
            data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabella chat/canali
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descrizione TEXT,
            tipo TEXT DEFAULT 'classe',
            classe TEXT,
            privata BOOLEAN DEFAULT 0,
            creatore_id INTEGER,
            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creatore_id) REFERENCES utenti (id)
        )
    ''')
    
    # Tabella messaggi
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messaggi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            utente_id INTEGER,
            contenuto TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT DEFAULT 'testo',
            file_allegato TEXT,
            modificato BOOLEAN DEFAULT 0,
            FOREIGN KEY (chat_id) REFERENCES chat (id),
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')
    
    # Tabella partecipanti chat
    conn.execute('''
        CREATE TABLE IF NOT EXISTS partecipanti_chat (
            chat_id INTEGER,
            utente_id INTEGER,
            ruolo_chat TEXT DEFAULT 'membro',
            data_aggiunta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (chat_id, utente_id),
            FOREIGN KEY (chat_id) REFERENCES chat (id),
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella per profili AI personalizzati
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER UNIQUE,
            bot_name TEXT DEFAULT 'CHEST Assistant',
            conversation_style TEXT DEFAULT 'friendly',
            learning_preferences TEXT,
            subject_strengths TEXT,
            subject_weaknesses TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella per conversazioni AI
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            feedback_rating INTEGER,
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    # Inserimento dati demo se non esistono
    admin_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE ruolo = "admin"').fetchone()[0]
    alessandro_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE email = "alessandro.demo@student.skaila.it"').fetchone()[0]
    
    if admin_exists == 0 or alessandro_exists == 0:
        # Crea admin di default
        admin_password = hash_password('admin123')
        conn.execute('''
            INSERT OR IGNORE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@skaila.it', admin_password, 'Admin', 'SKAILA', 'admin', 0))
        
        # Crea founder con credenziali facili
        founder_password = hash_password('founder123')
        conn.execute('''
            INSERT OR IGNORE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('founder', 'founder@skaila.it', founder_password, 'Daniele', 'Founder', 'admin', 0))
        
        # Crea professore demo
        prof_password = hash_password('prof123')
        conn.execute('''
            INSERT OR IGNORE INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('prof_rossi', 'prof.rossi@skaila.it', prof_password, 'Mario', 'Rossi', '3A', 'professore', 0))
        
        # Crea studenti demo
        stud_password = hash_password('stud123')
        studenti_demo = [
            ('alessandro_demo', 'alessandro.demo@student.skaila.it', 'Alessandro', 'Demo', '3A'),
            ('marco_bianchi', 'marco.bianchi@student.skaila.it', 'Marco', 'Bianchi', '3A'),
            ('giulia_verdi', 'giulia.verdi@student.skaila.it', 'Giulia', 'Verdi', '3A'),
            ('luca_ferrari', 'luca.ferrari@student.skaila.it', 'Luca', 'Ferrari', '3B'),
            ('sofia_romano', 'sofia.romano@student.skaila.it', 'Sofia', 'Romano', '3B')
        ]
        
        for username, email, nome, cognome, classe in studenti_demo:
            conn.execute('''
                INSERT OR IGNORE INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, stud_password, nome, cognome, classe, 'studente', 0))
        
        # Crea chat di classe
        conn.execute('''
            INSERT OR IGNORE INTO chat (nome, descrizione, tipo, classe)
            VALUES (?, ?, ?, ?)
        ''', ('Chat Classe 3A', 'Chat generale per la classe 3A', 'classe', '3A'))
        
        conn.execute('''
            INSERT OR IGNORE INTO chat (nome, descrizione, tipo, classe)
            VALUES (?, ?, ?, ?)
        ''', ('Chat Classe 3B', 'Chat generale per la classe 3B', 'classe', '3B'))
        
        # Aggiungi studenti alle chat di classe
        chat_3a = conn.execute('SELECT id FROM chat WHERE classe = "3A"').fetchone()
        chat_3b = conn.execute('SELECT id FROM chat WHERE classe = "3B"').fetchone()
        
        if chat_3a:
            utenti_3a = conn.execute('SELECT id FROM utenti WHERE classe = "3A"').fetchall()
            for utente in utenti_3a:
                conn.execute('''
                    INSERT OR IGNORE INTO partecipanti_chat (chat_id, utente_id)
                    VALUES (?, ?)
                ''', (chat_3a['id'], utente['id']))
        
        if chat_3b:
            utenti_3b = conn.execute('SELECT id FROM utenti WHERE classe = "3B"').fetchall()
            for utente in utenti_3b:
                conn.execute('''
                    INSERT OR IGNORE INTO partecipanti_chat (chat_id, utente_id)
                    VALUES (?, ?)
                ''', (chat_3b['id'], utente['id']))
        
        print("✅ Database inizializzato con dati demo")
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/chat')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"🔍 Login attempt - Email: {email}")
        
        conn = get_db_connection()
        
        # Prima verifica se l'utente esiste
        user = conn.execute('SELECT * FROM utenti WHERE email = ?', (email,)).fetchone()
        print(f"🔍 User found: {'Yes' if user else 'No'}")
        
        if user:
            print(f"🔍 User details - ID: {user['id']}, Nome: {user['nome']}, Attivo: {user['attivo']}")
            
            # Verifica password
            input_hash = hash_password(password)
            stored_hash = user['password_hash']
            print(f"🔍 Password check - Input hash: {input_hash[:20]}..., Stored hash: {stored_hash[:20]}...")
            print(f"🔍 Password match: {stored_hash == input_hash}")
            
            if stored_hash == input_hash and user['attivo'] == 1:
                # Login riuscito
                print(f"✅ Login successful for user: {user['nome']}")
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
                
                return redirect('/chat')
            else:
                print(f"❌ Login failed - Password mismatch or user not active")
        else:
            print(f"❌ Login failed - User not found")
        
        conn.close()
        return render_template('login.html', error='Email o password non corretti. Controlla di aver inserito le credenziali corrette.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            nome = request.form['nome']
            cognome = request.form['cognome']
            classe = request.form.get('classe', '')
            
            conn = get_db_connection()
            
            # Controlla se utente esiste già
            existing_user = conn.execute('SELECT id FROM utenti WHERE email = ? OR username = ?', (email, username)).fetchone()
            if existing_user:
                conn.close()
                return render_template('register.html', error='Email o username già esistenti')
            
            # Crea nuovo utente
            password_hash = hash_password(password)
            conn.execute('''
                INSERT INTO utenti (username, email, password_hash, nome, cognome, classe)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, nome, cognome, classe))
            
            conn.commit()
            conn.close()
            
            flash('Registrazione completata! Puoi ora effettuare il login.', 'success')
            return redirect('/login')
            
        except Exception as e:
            return render_template('register.html', error=f'Errore durante la registrazione: {str(e)}')
    
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    
    # Ottieni chat dell'utente
    if session['ruolo'] == 'admin':
        chats = conn.execute('SELECT * FROM chat ORDER BY nome').fetchall()
    else:
        chats = conn.execute('''
            SELECT c.* FROM chat c
            JOIN partecipanti_chat pc ON c.id = pc.chat_id
            WHERE pc.utente_id = ? OR c.classe = ?
            ORDER BY c.nome
        ''', (session['user_id'], session.get('classe', ''))).fetchall()
    
    # Ottieni utenti online
    utenti_online = conn.execute('''
        SELECT nome, cognome, ruolo, classe FROM utenti 
        WHERE status_online = 1 AND id != ?
        ORDER BY nome
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('chat.html', 
                         user=session, 
                         chats=chats, 
                         utenti_online=utenti_online)

@app.route('/ai-chat')
def ai_chat():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('ai_chat.html', user=session)

@app.route('/api/ai-chat', methods=['POST'])
def api_ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message.strip():
            return jsonify({'error': 'Messaggio vuoto'}), 400
        
        # Ottieni o crea profilo AI per l'utente
        conn = get_db_connection()
        profile = conn.execute('SELECT * FROM ai_profiles WHERE utente_id = ?', 
                             (session['user_id'],)).fetchone()
        
        if not profile:
            # Crea nuovo profilo
            conn.execute('''
                INSERT INTO ai_profiles (utente_id, bot_name, conversation_style)
                VALUES (?, ?, ?)
            ''', (session['user_id'], 'CHEST Assistant', 'friendly'))
            conn.commit()
            profile = conn.execute('SELECT * FROM ai_profiles WHERE utente_id = ?', 
                                 (session['user_id'],)).fetchone()
        
        # Genera risposta AI
        response = ai_bot.generate_response(
            message, 
            session['nome'], 
            session['ruolo'],
            profile['conversation_style']
        )
        
        # Salva conversazione
        conn.execute('''
            INSERT INTO ai_conversations (utente_id, message, response)
            VALUES (?, ?, ?)
        ''', (session['user_id'], message, response))
        conn.commit()
        conn.close()
        
        return jsonify({
            'response': response,
            'bot_name': profile['bot_name']
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore del server: {str(e)}'}), 500

@app.route('/logout')
def logout():
    if 'user_id' in session:
        conn = get_db_connection()
        conn.execute('UPDATE utenti SET status_online = 0 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
    
    session.clear()
    return redirect('/')

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")
        
        conn = get_db_connection()
        conn.execute('UPDATE utenti SET status_online = 1 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
        
        emit('user_connected', {
            'nome': session['nome'],
            'cognome': session['cognome'],
            'ruolo': session['ruolo']
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        leave_room(f"user_{session['user_id']}")
        
        conn = get_db_connection()
        conn.execute('UPDATE utenti SET status_online = 0 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
        
        emit('user_disconnected', {
            'nome': session['nome'],
            'cognome': session['cognome']
        }, broadcast=True)

@socketio.on('join_chat')
def handle_join_chat(data):
    if 'user_id' not in session:
        return
    
    chat_id = data['chat_id']
    join_room(f"chat_{chat_id}")
    
    # Carica messaggi recenti
    conn = get_db_connection()
    messaggi = conn.execute('''
        SELECT m.*, u.nome, u.cognome, u.ruolo 
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        WHERE m.chat_id = ?
        ORDER BY m.timestamp DESC
        LIMIT 50
    ''', (chat_id,)).fetchall()
    conn.close()
    
    # Inverti ordine per mostrare dal più vecchio al più nuovo
    messaggi = list(reversed(messaggi))
    
    emit('messaggi_caricati', {
        'messaggi': [dict(msg) for msg in messaggi]
    })

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    
    chat_id = data['chat_id']
    contenuto = data['contenuto']
    
    # Salva messaggio nel database
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO messaggi (chat_id, utente_id, contenuto)
        VALUES (?, ?, ?)
    ''', (chat_id, session['user_id'], contenuto))
    conn.commit()
    
    # Ottieni il messaggio appena inserito con i dati utente
    messaggio = conn.execute('''
        SELECT m.*, u.nome, u.cognome, u.ruolo 
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        WHERE m.chat_id = ? AND m.utente_id = ?
        ORDER BY m.timestamp DESC
        LIMIT 1
    ''', (chat_id, session['user_id'])).fetchone()
    conn.close()
    
    # Invia a tutti nella chat
    emit('nuovo_messaggio', dict(messaggio), room=f"chat_{chat_id}")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
