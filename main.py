import sqlite3
import hashlib
from flask import Flask, render_template, request, redirect, session, flash, jsonify, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import openai
from ai_chatbot import AISkailaBot
from gamification import gamification_system

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skaila_secret_key_super_secure_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configurazione sessioni permanenti
app.permanent_session_lifetime = timedelta(days=30)

# Configurazione per Replit Webview
@app.after_request
def after_request(response):
    # Headers per permettere iframe in Replit
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.replit.com *.repl.co"

    # Headers per CORS
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

    # Cache control per sviluppo
    if app.debug:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response

socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   logger=True, 
                   engineio_logger=True,
                   allow_upgrades=True,
                   transports=['websocket', 'polling'])

# Inizializza il chatbot AI personalizzato
ai_bot = AISkailaBot()

# Inizializza sistema gamification
gamification_system.init_gamification_tables()

# Utility per password hashing avanzato
import secrets
import time
from functools import wraps

def hash_password(password):
    """Hash sicuro con salt per produzione"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verifica password con bcrypt"""
    import bcrypt
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        # Fallback per hash SHA-256 esistenti durante migrazione
        return hashlib.sha256(password.encode()).hexdigest() == hashed

def rate_limit_login(f):
    """Rate limiting per tentativi di login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

        # Controlla tentativi recenti
        conn = get_db_connection()
        recent_attempts = conn.execute('''
            SELECT COUNT(*) FROM login_attempts 
            WHERE ip_address = ? AND timestamp > datetime('now', '-15 minutes')
        ''', (client_ip,)).fetchone()[0]

        if recent_attempts >= 10:  # Max 10 tentativi in 15 minuti
            conn.close()
            return render_template('login.html', 
                error='Troppi tentativi di login. Riprova tra 15 minuti.')

        conn.close()
        return f(*args, **kwargs)
    return decorated_function

def log_login_attempt(email, success, ip_address):
    """Log dei tentativi di login per sicurezza"""
    conn = get_db_connection()

    # Crea tabella se non esiste
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            success BOOLEAN,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT
        )
    ''')

    conn.execute('''
        INSERT INTO login_attempts (email, success, ip_address, user_agent)
        VALUES (?, ?, ?, ?)
    ''', (email, success, ip_address, request.headers.get('User-Agent', '')))

    conn.commit()
    conn.close()

# Database connection ottimizzata
def get_db_connection():
    conn = sqlite3.connect('skaila.db', timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Ottimizzazioni SQLite per performance
    conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
    conn.execute('PRAGMA synchronous=NORMAL')  # Bilanciamento sicurezza/velocità
    conn.execute('PRAGMA cache_size=10000')   # Cache più grande
    conn.execute('PRAGMA temp_store=memory')  # Tabelle temporanee in RAM
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

    # Tabella per profili AI personalizzati - ENHANCED
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER UNIQUE,
            bot_name TEXT DEFAULT 'SKAILA Assistant',
            bot_avatar TEXT DEFAULT '🤖',
            conversation_style TEXT DEFAULT 'friendly',
            learning_preferences TEXT DEFAULT 'adaptive',
            difficulty_preference TEXT DEFAULT 'medium',
            subject_strengths TEXT,
            subject_weaknesses TEXT,
            personality_traits TEXT,
            study_schedule TEXT,
            preferred_examples TEXT DEFAULT 'mixed',
            interaction_goals TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_interactions INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella per conversazioni AI - ENHANCED
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            subject_detected TEXT,
            difficulty_level TEXT,
            sentiment_analysis TEXT,
            learning_objective TEXT,
            success_metric REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            feedback_rating INTEGER,
            interaction_duration INTEGER,
            follow_up_needed BOOLEAN DEFAULT 0,
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    # Tabella per tracking di apprendimento
    conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER,
            subject TEXT,
            skill_level TEXT,
            progress_percentage REAL DEFAULT 0.0,
            time_spent_minutes INTEGER DEFAULT 0,
            exercises_completed INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            streak_days INTEGER DEFAULT 0,
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    # Inserimento dati demo se non esistono
    admin_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE ruolo = "admin"').fetchone()[0]
    founder_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE email = "founder@skaila.it"').fetchone()[0]

    print(f"🔍 Database check - Admin exists: {admin_exists}, Founder exists: {founder_exists}")

    if admin_exists == 0 or founder_exists == 0:
        print("🔧 Creating default users...")

        # Crea admin di default
        admin_password = hash_password('admin123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@skaila.it', admin_password, 'Admin', 'SKAILA', 'admin', 0))
            print("✅ Admin user created")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")

        # Crea founder con credenziali facili
        founder_password = hash_password('founder123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('founder', 'founder@skaila.it', founder_password, 'Daniele', 'Founder', 'admin', 0))
            print("✅ Founder user created")
        except Exception as e:
            print(f"❌ Error creating founder: {e}")

        # Crea account per papà con credenziali semplici
        papa_password = hash_password('papa123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('papa', 'papa@skaila.it', papa_password, 'Papà', 'Famiglia', 'genitore', 0))
            print("✅ Papa user created")
        except Exception as e:
            print(f"❌ Error creating papa: {e}")

        # Crea account per mamma con credenziali semplici
        mamma_password = hash_password('mamma123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('mamma', 'mamma@skaila.it', mamma_password, 'Mamma', 'Famiglia', 'genitore', 0))
            print("✅ Mamma user created")
        except Exception as e:
            print(f"❌ Error creating mamma: {e}")

        # Crea account demo per test operativi con credenziali semplici
        demo1_password = hash_password('test123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('alice_demo', 'alice@test.skaila.it', demo1_password, 'Alice', 'Demo', '3A', 'studente', 0))
            print("✅ Alice Demo user created")
        except Exception as e:
            print(f"❌ Error creating Alice Demo: {e}")

        demo2_password = hash_password('test123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('bob_demo', 'bob@test.skaila.it', demo2_password, 'Bob', 'Demo', '3B', 'studente', 0))
            print("✅ Bob Demo user created")
        except Exception as e:
            print(f"❌ Error creating Bob Demo: {e}")

        # Account professore demo per test
        prof_demo_password = hash_password('prof123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('prof_demo', 'prof@test.skaila.it', prof_demo_password, 'Prof', 'Demo', '3A', 'professore', 0))
            print("✅ Prof Demo user created")
        except Exception as e:
            print(f"❌ Error creating Prof Demo: {e}")

        # Account genitore demo per test
        genitore_demo_password = hash_password('parent123')
        try:
            conn.execute('''
                INSERT OR REPLACE INTO utenti (username, email, password_hash, nome, cognome, ruolo, primo_accesso)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('parent_demo', 'parent@test.skaila.it', genitore_demo_password, 'Parent', 'Demo', 'genitore', 0))
            print("✅ Parent Demo user created")
        except Exception as e:
            print(f"❌ Error creating Parent Demo: {e}")

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

        # Crea chat tematiche e generali
        chat_rooms = [
            ('💬 Chat Generale SKAILA', 'Chat generale per tutti gli utenti della piattaforma', 'generale', ''),
            ('📚 Aiuto Compiti', 'Chat per ricevere e dare aiuto con i compiti', 'tematica', ''),
            ('💻 Informatica & Coding', 'Discussioni su programmazione e tecnologia', 'tematica', ''),
            ('🧮 Matematica & Fisica', 'Gruppo di studio per materie scientifiche', 'tematica', ''),
            ('📖 Letteratura & Storia', 'Chat per appassionati di materie umanistiche', 'tematica', ''),
            ('🌍 Inglese & Lingue', 'Pratichiamo le lingue straniere insieme', 'tematica', ''),
            ('🎨 Creatività & Arte', 'Condividi i tuoi progetti creativi', 'tematica', ''),
            ('📈 Digital Marketing', 'Strategie, campagne e trend del marketing digitale', 'tematica', ''),
            ('₿ Crypto e Blockchain', 'Discussioni su criptovalute, NFT e tecnologie blockchain', 'tematica', ''),
            ('⚖️ Fiscalità e Legalità', 'Consulenza fiscale, diritto e aspetti legali', 'tematica', ''),
            ('🌱 Sostenibilità Ambientale', 'Progetti green, economia circolare e ambiente', 'tematica', ''),
            ('🏆 Gamification SKAILA', 'Sfide, classifiche e achievement', 'evento', ''),
            ('👥 Rappresentanti di Classe', 'Chat riservata ai rappresentanti', 'organizzativo', ''),
            ('📢 Annunci Scuola', 'Comunicazioni ufficiali dell\'istituto', 'ufficiale', '')
        ]

        for nome, descrizione, tipo, classe in chat_rooms:
            conn.execute('''
                INSERT OR IGNORE INTO chat (nome, descrizione, tipo, classe)
                VALUES (?, ?, ?, ?)
            ''', (nome, descrizione, tipo, classe))

        # Ottieni tutti gli utenti e tutte le chat
        tutti_utenti = conn.execute('SELECT id, ruolo FROM utenti').fetchall()
        tutte_chat = conn.execute('SELECT id, tipo, classe FROM chat').fetchall()

        # Aggiungi utenti alle chat appropriate
        for utente in tutti_utenti:
            user_id = utente['id']
            user_role = utente['ruolo']

            for chat in tutte_chat:
                chat_id = chat['id']
                chat_tipo = chat['tipo']
                chat_classe = chat['classe']

                # Logica di assegnazione chat
                should_add = False
                ruolo_chat = 'membro'

                # Admin e founder in tutte le chat
                if user_role in ['admin']:
                    should_add = True
                    ruolo_chat = 'admin'

                # Chat generali e tematiche per tutti
                elif chat_tipo in ['generale', 'tematica', 'evento']:
                    should_add = True

                # Chat di classe solo per studenti della classe
                elif chat_tipo == 'classe' and chat_classe:
                    user_classe = conn.execute('SELECT classe FROM utenti WHERE id = ?', (user_id,)).fetchone()
                    if user_classe and user_classe['classe'] == chat_classe:
                        should_add = True

                # Chat organizzative per rappresentanti e professori
                elif chat_tipo == 'organizzativo' and user_role in ['professore', 'admin']:
                    should_add = True
                    ruolo_chat = 'moderatore'

                # Chat ufficiali per tutti, ma solo admin possono scrivere
                elif chat_tipo == 'ufficiale':
                    should_add = True
                    ruolo_chat = 'admin' if user_role == 'admin' else 'lettore'

                if should_add:
                    conn.execute('''
                        INSERT OR IGNORE INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
                        VALUES (?, ?, ?)
                    ''', (chat_id, user_id, ruolo_chat))

        conn.commit()
        conn.close()
        print("✅ Database inizializzato con dati demo")

        # Verifica che gli utenti siano stati creati
        verify_users = conn.execute('SELECT email, nome FROM utenti WHERE email IN (?, ?)', 
                                  ('admin@skaila.it', 'founder@skaila.it')).fetchall()
        print(f"🔍 Users created: {[dict(u) for u in verify_users]}")

    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"🔍 Login attempt - Email: {email}")

        conn = get_db_connection()

        # Verifica se l'utente esiste nel database
        user = conn.execute('SELECT * FROM utenti WHERE email = ?', (email,)).fetchone()
        print(f"🔍 User found: {'Yes' if user else 'No'}")

        # Se non trova l'utente, mostra tutti gli utenti per debug
        if not user:
            all_users = conn.execute('SELECT email, nome FROM utenti LIMIT 5').fetchall()
            print(f"🔍 Available users in DB: {[dict(u) for u in all_users]}")

        if user:
            print(f"🔍 User details - ID: {user['id']}, Nome: {user['nome']}, Attivo: {user['attivo']}")

            # Verifica password con sistema avanzato
            password_valid = verify_password(password, user['password_hash'])
            print(f"🔍 Password verification: {'✅ Valid' if password_valid else '❌ Invalid'}")
            print(f"🔍 User active: {user['attivo'] == 1}")

            if password_valid and user['attivo'] == 1:
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

                # Sistema Gamification - Login giornaliero
                try:
                    gamification_system.get_or_create_user_profile(user['id'])
                    streak_info = gamification_system.update_streak(user['id'])

                    if streak_info and streak_info.get('streak_updated'):
                        if streak_info.get('current_streak') == 1 and not streak_info.get('streak_broken', False):
                            gamification_system.award_xp(user['id'], 'first_login_day', description="Primo accesso della giornata!")
                        else:
                            gamification_system.award_xp(user['id'], 'login_daily', description="Login giornaliero")
                    else:
                        # Fallback se gamification non funziona
                        gamification_system.award_xp(user['id'], 'login_daily', description="Login giornaliero")
                except Exception as gamification_error:
                    print(f"⚠️ Gamification error durante login: {gamification_error}")
                    # Il login continua anche se gamification fallisce

                return redirect('/dashboard')
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
            # Controlla se c'è un codice scuola per registrazione di massa
            school_code = request.form.get('school_code', '')

            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            nome = request.form['nome']
            cognome = request.form['cognome']
            classe = request.form.get('classe', '')
            ruolo = request.form.get('ruolo', 'studente')
            scuola = request.form.get('scuola', '')

            conn = get_db_connection()

            # Verifica codice scuola per registrazioni di massa
            if school_code:
                valid_school = conn.execute('''
                    SELECT nome_scuola FROM school_codes 
                    WHERE code = ? AND attivo = 1 AND expires_at > CURRENT_TIMESTAMP
                ''', (school_code,)).fetchone()

                if not valid_school:
                    conn.close()
                    return render_template('register.html', error='Codice scuola non valido o scaduto')

                scuola = valid_school['nome_scuola']

            # Controlla se utente esiste già
            existing_user = conn.execute('SELECT id FROM utenti WHERE email = ? OR username = ?', (email, username)).fetchone()
            if existing_user:
                conn.close()
                return render_template('register.html', error='Email o username già esistenti')

            # Validazione email scuola per domini autorizzati
            if scuola:
                school_domains = conn.execute('''
                    SELECT authorized_domains FROM schools WHERE nome = ?
                ''', (scuola,)).fetchone()

                if school_domains and school_domains['authorized_domains']:
                    authorized = any(domain.strip() in email for domain in school_domains['authorized_domains'].split(','))
                    if not authorized and ruolo in ['professore', 'admin']:
                        conn.close()
                        return render_template('register.html', error='Email non autorizzata per questo ruolo nella scuola')

            # Crea nuovo utente con validazioni avanzate
            password_hash = hash_password(password)
            cursor = conn.execute('''
                INSERT INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, scuola, 
                                   primo_accesso, data_registrazione)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', (username, email, password_hash, nome, cognome, classe, ruolo, scuola))

            user_id = cursor.lastrowid

            # Auto-assegnazione a chat appropriate basate su ruolo e classe
            if ruolo == 'studente' and classe:
                # Aggiungi a chat di classe
                chat_classe = conn.execute('''
                    SELECT id FROM chat WHERE classe = ? AND tipo = 'classe'
                ''', (classe,)).fetchone()

                if chat_classe:
                    conn.execute('''
                        INSERT INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
                        VALUES (?, ?, 'membro')
                    ''', (chat_classe['id'], user_id))

            # Aggiungi a chat generali per tutti
            chat_generali = conn.execute('''
                SELECT id FROM chat WHERE tipo IN ('generale', 'tematica') AND privata = 0
            ''').fetchall()

            for chat in chat_generali:
                conn.execute('''
                    INSERT OR IGNORE INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
                    VALUES (?, ?, 'membro')
                ''', (chat['id'], user_id))

            # Crea profilo AI personalizzato
            conn.execute('''
                INSERT INTO ai_profiles (utente_id, bot_name, conversation_style)
                VALUES (?, ?, ?)
            ''', (user_id, f'SKAILA Assistant per {nome}', 'friendly'))

            conn.commit()
            conn.close()

            # Auto-login dopo registrazione
            session.permanent = True
            session['user_id'] = user_id
            session['username'] = username
            session['nome'] = nome
            session['cognome'] = cognome
            session['ruolo'] = ruolo
            session['email'] = email
            session['classe'] = classe
            session['primo_accesso'] = True  # Flag per onboarding

            flash('Registrazione completata con successo! 🎉', 'success')
            return redirect('/onboarding')

        except Exception as e:
            return render_template('register.html', error=f'Errore durante la registrazione: {str(e)}')

    return render_template('register.html')

@app.route('/admin/bulk-register', methods=['GET', 'POST'])
def admin_bulk_register():
    """Sistema di registrazione di massa per amministratori scuola"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        try:
            # CSV upload per registrazione di massa
            csv_data = request.form.get('csv_data', '')
            school_name = request.form.get('school_name', '')
            default_password = request.form.get('default_password', 'scuola123')

            conn = get_db_connection()
            registered_count = 0
            errors = []

            # Processa CSV: nome,cognome,email,classe,ruolo
            for line_num, line in enumerate(csv_data.strip().split('\n'), 1):
                if not line.strip():
                    continue

                try:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4:
                        nome, cognome, email, classe = parts[:4]
                        ruolo = parts[4] if len(parts) > 4 else 'studente'
                        username = f"{nome.lower()}.{cognome.lower()}"

                        # Controlla duplicati
                        existing = conn.execute('SELECT id FROM utenti WHERE email = ?', (email,)).fetchone()
                        if not existing:
                            password_hash = hash_password(default_password)
                            conn.execute('''
                                INSERT INTO utenti (username, email, password_hash, nome, cognome, 
                                                   classe, ruolo, scuola, primo_accesso)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                            ''', (username, email, password_hash, nome, cognome, classe, ruolo, school_name))
                            registered_count += 1
                        else:
                            errors.append(f"Riga {line_num}: Email {email} già esistente")
                    else:
                        errors.append(f"Riga {line_num}: Formato non valido")

                except Exception as e:
                    errors.append(f"Riga {line_num}: {str(e)}")

            conn.commit()
            conn.close()

            if errors:
                flash(f'Registrati {registered_count} utenti. Errori: {"; ".join(errors[:5])}', 'warning')
            else:
                flash(f'Registrazione di massa completata! {registered_count} utenti registrati.', 'success')

        except Exception as e:
            flash(f'Errore nella registrazione di massa: {str(e)}', 'error')

    return render_template('admin_bulk_register.html')

@app.route('/api/school/invite-code', methods=['POST'])
def create_school_invite():
    """Crea codici invito per scuole"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        school_name = data.get('school_name')
        expires_days = data.get('expires_days', 30)
        max_uses = data.get('max_uses', 1000)

        import secrets
        invite_code = secrets.token_urlsafe(12).upper()

        conn = get_db_connection()

        # Crea tabella se non esiste
        conn.execute('''
            CREATE TABLE IF NOT EXISTS school_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                nome_scuola TEXT NOT NULL,
                max_uses INTEGER DEFAULT 1000,
                current_uses INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                attivo BOOLEAN DEFAULT 1,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES utenti (id)
            )
        ''')

        conn.execute('''
            INSERT INTO school_codes (code, nome_scuola, max_uses, expires_at, created_by)
            VALUES (?, ?, ?, datetime('now', '+{} days'), ?)
        '''.format(expires_days), (invite_code, school_name, max_uses, session['user_id']))

        conn.commit()
        conn.close()

        return jsonify({
            'invite_code': invite_code,
            'school_name': school_name,
            'expires_days': expires_days,
            'max_uses': max_uses
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/onboarding')
def onboarding():
    if 'user_id' not in session:
        return redirect('/login')

    # Solo per utenti al primo accesso
    if not session.get('primo_accesso', False):
        return redirect('/chat')

    return render_template('onboarding.html', user=session)

@app.route('/complete-onboarding', methods=['POST'])
def complete_onboarding():
    if 'user_id' not in session:
        return redirect('/login')

    # Aggiorna flag primo accesso
    conn = get_db_connection()
    conn.execute('''
        UPDATE utenti 
        SET primo_accesso = 0 
        WHERE id = ?
    ''', (session['user_id'],))
    conn.commit()
    conn.close()

    session['primo_accesso'] = False
    return redirect('/chat')

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

@app.route('/gamification')
def gamification_dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    # Aggiungi header per permettere embedding
    response = make_response(render_template('gamification_dashboard.html', user=session))
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
    return response

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    # Qui verrebbero caricati i dati specifici della dashboard
    # Ad esempio, statistiche chiave, notifiche, ecc.

    # Per ora, restituisce un template di base per la dashboard
    return render_template('dashboard.html', user=session)


@app.route('/api/conversations')
def api_conversations():
    if 'user_id' not in session:
        print(f"❌ API /api/conversations - No user_id in session")
        print(f"🔍 Session contents: {dict(session)}")
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        print(f"✅ API /api/conversations - User: {session.get('nome', 'Unknown')}")
        conn = get_db_connection()

        # Ottieni chat dell'utente
        if session['ruolo'] == 'admin':
            conversations = conn.execute('''
                SELECT c.*, 
                       COUNT(DISTINCT pc.utente_id) as partecipanti_count,
                       m.contenuto as ultimo_messaggio,
                       m.timestamp as ultimo_messaggio_data,
                       u.nome || ' ' || u.cognome as ultimo_mittente
                FROM chat c
                LEFT JOIN partecipanti_chat pc ON c.id = pc.chat_id
                LEFT JOIN messaggi m ON c.id = m.chat_id 
                    AND m.timestamp = (SELECT MAX(timestamp) FROM messaggi WHERE chat_id = c.id)
                LEFT JOIN utenti u ON m.utente_id = u.id
                GROUP BY c.id
                ORDER BY ultimo_messaggio_data DESC NULLS LAST
            ''').fetchall()
        else:
            conversations = conn.execute('''
                SELECT c.*, 
                       COUNT(DISTINCT pc.utente_id) as partecipanti_count,
                       m.contenuto as ultimo_messaggio,
                       m.timestamp as ultimo_messaggio_data,
                       u.nome || ' ' || u.cognome as ultimo_mittente,
                       0 as messaggi_non_letti
                FROM chat c
                JOIN partecipanti_chat pc ON c.id = pc.chat_id
                LEFT JOIN messaggi m ON c.id = m.chat_id 
                    AND m.timestamp = (SELECT MAX(timestamp) FROM messaggi WHERE chat_id = c.id)
                LEFT JOIN utenti u ON m.utente_id = u.id
                WHERE pc.utente_id = ? OR c.classe = ?
                GROUP BY c.id
                ORDER BY ultimo_messaggio_data DESC NULLS LAST
            ''', (session['user_id'], session.get('classe', ''))).fetchall()

        conn.close()
        conversations_list = [dict(conv) for conv in conversations]
        print(f"🔍 Found {len(conversations_list)} conversations for user")
        return jsonify(conversations_list)

    except Exception as e:
        print(f"❌ Error in /api/conversations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<int:conversation_id>')
def api_messages(conversation_id):
    if 'user_id' not in session:
        print(f"❌ API /api/messages - No user_id in session")
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        print(f"✅ API /api/messages - User: {session.get('nome', 'Unknown')}, Chat: {conversation_id}")
        conn = get_db_connection()

        messages = conn.execute('''
            SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
                   m.timestamp as data_invio
            FROM messaggi m
            JOIN utenti u ON m.utente_id = u.id
            WHERE m.chat_id = ?
            ORDER BY m.timestamp ASC
            LIMIT 100
        ''', (conversation_id,)).fetchall()

        conn.close()
        messages_list = [dict(msg) for msg in messages]
        print(f"🔍 Found {len(messages_list)} messages in chat {conversation_id}")
        return jsonify(messages_list)

    except Exception as e:
        print(f"❌ Error in /api/messages: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/search')
def api_users_search():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    try:
        conn = get_db_connection()

        users = conn.execute('''
            SELECT id, username, nome, cognome, ruolo, classe, status_online
            FROM utenti 
            WHERE (nome LIKE ? OR cognome LIKE ? OR username LIKE ?) 
                  AND id != ? AND attivo = 1
            ORDER BY nome, cognome
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', session['user_id'])).fetchall()

        conn.close()
        return jsonify([dict(user) for user in users])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/create', methods=['POST'])
def api_create_conversation():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        tipo = data.get('tipo', 'privata')
        partecipanti = data.get('partecipanti', [])

        conn = get_db_connection()

        # Crea conversazione
        cursor = conn.execute('''
            INSERT INTO chat (nome, tipo, privata, creatore_id)
            VALUES (?, ?, ?, ?)
        ''', (f'Chat {datetime.now().strftime("%d/%m %H:%M")}', tipo, 1, session['user_id']))

        conversation_id = cursor.lastrowid

        # Aggiungi creatore
        conn.execute('''
            INSERT INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
            VALUES (?, ?, ?)
        ''', (conversation_id, session['user_id'], 'admin'))

        # Aggiungi partecipanti
        for user_id in partecipanti:
            conn.execute('''
                INSERT INTO partecipanti_chat (chat_id, utente_id)
                VALUES (?, ?)
            ''', (conversation_id, user_id))



        conn.commit()
        conn.close()

        return jsonify({'conversation_id': conversation_id})

    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/quiz', methods=['POST'])
def api_ai_quiz():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        subject = data.get('subject', 'general')
        difficulty = data.get('difficulty', 'adaptive')

        print(f"🧠 Generating personalized quiz - Subject: {subject}, Difficulty: {difficulty}")

        # Carica profilo utente
        user_profile = ai_bot.load_user_profile(session['user_id'])

        # Genera domanda personalizzata
        question_data = ai_bot.generate_adaptive_quiz_question(subject, user_profile, difficulty)

        # Salva nel database per tracking
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ai_conversations 
            (utente_id, message, response, subject_detected, difficulty_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], f"Quiz Request: {subject}", 
              f"Generated quiz question", subject, difficulty))
        conn.commit()
        conn.close()

        return jsonify({
            'question': question_data,
            'personalized': True,
            'adapted_difficulty': difficulty,
            'bot_name': user_profile.get('bot_name', 'SKAILA Assistant')
        })

    except Exception as e:
        print(f"❌ Error generating personalized quiz: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/feedback', methods=['POST'])
def api_ai_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        rating = data.get('rating', 3)
        message_id = data.get('message_id')
        feedback_text = data.get('feedback', '')

        conn = get_db_connection()

        # Aggiorna il rating della conversazione
        if message_id:
            conn.execute('''
                UPDATE ai_conversations 
                SET feedback_rating = ? 
                WHERE id = ? AND utente_id = ?
            ''', (rating, message_id, session['user_id']))

        # Aggiorna il success rate nel profilo
        avg_rating = conn.execute('''
            SELECT AVG(feedback_rating) FROM ai_conversations 
            WHERE utente_id = ? AND feedback_rating IS NOT NULL
        ''', (session['user_id'],)).fetchone()[0]

        if avg_rating:
            conn.execute('''
                UPDATE ai_profiles 
                SET success_rate = ? 
                WHERE utente_id = ?
            ''', (avg_rating, session['user_id']))

        conn.commit()
        conn.close()

        # Gamification - Feedback positivo
        if rating >= 4:
            gamification_system.award_xp(session['user_id'], 'ai_correct_answer', description="Feedback positivo AI!")

        return jsonify({'success': True, 'message': 'Feedback salvato!'})

    except Exception as e:
        print(f"❌ Error saving AI feedback: {e}")
        return jsonify({'error': str(e)}), 500


# ========== API GAMIFICATION COMPLETE ==========

@app.route('/api/gamification/dashboard')
def api_gamification_dashboard():
    """Dashboard completa gamification per l'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        dashboard_data = gamification_system.get_user_dashboard(session['user_id'])
        return jsonify(dashboard_data)

    except Exception as e:
        print(f"❌ Error loading gamification dashboard: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API SISTEMA AVATAR ==========

@app.route('/api/gamification/avatar/available')
def api_available_avatars():
    """Ottieni avatar disponibili per l'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        avatars = gamification_system.get_available_avatars(session['user_id'])
        return jsonify({'avatars': avatars})

    except Exception as e:
        print(f"❌ Error loading available avatars: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/avatar/purchase', methods=['POST'])
def api_purchase_avatar():
    """Acquista un avatar con le monete"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        avatar_id = data.get('avatar_id')

        result = gamification_system.purchase_avatar(session['user_id'], avatar_id)
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error purchasing avatar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/avatar/change', methods=['POST'])
def api_change_avatar():
    """Cambia avatar dell'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        avatar_id = data.get('avatar_id')

        result = gamification_system.change_avatar(session['user_id'], avatar_id)
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error changing avatar: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API SFIDE COLLABORATIVE ==========

@app.route('/api/gamification/team-challenges')
def api_team_challenges():
    """Ottieni sfide di squadra attive"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        user_class = session.get('classe')
        challenges = gamification_system.get_active_team_challenges(user_class)
        return jsonify({'challenges': challenges})

    except Exception as e:
        print(f"❌ Error loading team challenges: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/team-challenge/create', methods=['POST'])
def api_create_team_challenge():
    """Crea una nuova sfida tra squadre (solo admin)"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        challenge_type = data.get('challenge_type')
        class_a = data.get('class_a')
        class_b = data.get('class_b')

        result = gamification_system.create_team_challenge(challenge_type, class_a, class_b)
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error creating team challenge: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/team-challenge/join', methods=['POST'])
def api_join_team_challenge():
    """Unisciti a una sfida di squadra"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        challenge_id = data.get('challenge_id')

        result = gamification_system.join_team_challenge(session['user_id'], challenge_id)
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error joining team challenge: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API ANALYTICS AVANZATE ==========

@app.route('/api/gamification/analytics')
def api_user_analytics():
    """Ottieni analytics dettagliate dell'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        days = request.args.get('days', 30, type=int)
        analytics = gamification_system.get_user_analytics(session['user_id'], days)
        return jsonify(analytics)

    except Exception as e:
        print(f"❌ Error loading user analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/analytics/record', methods=['POST'])
def api_record_activity():
    """Registra attività per analytics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        activity_type = data.get('activity_type')
        value = data.get('value', 1)

        gamification_system.record_daily_activity(session['user_id'], activity_type, value)
        return jsonify({'success': True, 'message': 'Attività registrata'})

    except Exception as e:
        print(f"❌ Error recording activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/leaderboard')
def api_gamification_leaderboard():
    """Classifica gamification"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        period = request.args.get('period', 'weekly')
        class_filter = request.args.get('class_filter', session.get('classe'))

        leaderboard_data = gamification_system.get_leaderboard(
            session['user_id'], 
            period, 
            class_filter
        )
        return jsonify(leaderboard_data)

    except Exception as e:
        print(f"❌ Error loading leaderboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/award-xp', methods=['POST'])
def api_award_xp():
    """Assegna XP per azioni specifiche"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        action_type = data.get('action_type')
        bonus_multiplier = data.get('bonus_multiplier', 1.0)
        description = data.get('description', '')

        result = gamification_system.award_xp(
            session['user_id'], 
            action_type, 
            bonus_multiplier, 
            description
        )

        return jsonify(result)

    except Exception as e:
        print(f"❌ Error awarding XP: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/challenges')
def api_daily_challenges():
    """Ottieni sfide giornaliere dell'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        challenges = gamification_system.get_daily_challenges(session['user_id'])
        return jsonify({'challenges': challenges})

    except Exception as e:
        print(f"❌ Error loading daily challenges: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/challenge-progress', methods=['POST'])
def api_update_challenge_progress():
    """Aggiorna progresso sfida giornaliera"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        challenge_type = data.get('challenge_type')
        increment = data.get('increment', 1)

        result = gamification_system.update_challenge_progress(
            session['user_id'], 
            challenge_type, 
            increment
        )

        return jsonify(result)

    except Exception as e:
        print(f"❌ Error updating challenge progress: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gamification/profile')
def api_gamification_profile():
    """Profilo gamification dell'utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        profile = gamification_system.get_or_create_user_profile(session['user_id'])

        # Aggiungi informazioni di livello
        profile['level_title'] = gamification_system.level_titles[profile['current_level']]

        next_level = profile['current_level'] + 1 if profile['current_level'] < 10 else 10
        next_level_xp = gamification_system.level_thresholds.get(next_level, gamification_system.level_thresholds[10])
        profile['next_level_xp'] = next_level_xp
        profile['level_progress'] = min(100, (profile['total_xp'] / next_level_xp) * 100) if next_level_xp > 0 else 100

        return jsonify(profile)

    except Exception as e:
        print(f"❌ Error loading gamification profile: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/profile')
def api_ai_profile():
    if 'user_id' not in session:
        print(f"❌ API /api/ai/profile - No user_id in session")
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        print(f"✅ API /api/ai/profile - User: {session.get('nome', 'Unknown')}")
        conn = get_db_connection()

        profile = conn.execute('''
            SELECT * FROM ai_profiles WHERE utente_id = ?
        ''', (session['user_id'],)).fetchone()

        if not profile:
            print(f"🔧 Creating enhanced AI profile for user {session['user_id']}")
            # Crea profilo avanzato di default
            conn.execute('''
                INSERT INTO ai_profiles (
                    utente_id, bot_name, bot_avatar, conversation_style, learning_preferences, difficulty_preference, subject_strengths, subject_weaknesses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], 'SKAILA Assistant', '🤖', 'friendly', 'adaptive', 'medium', '', ''))
            conn.commit()

            profile = conn.execute('''
                SELECT * FROM ai_profiles WHERE utente_id = ?
            ''', (session['user_id'],)).fetchone()

        conn.close()

        # Convert Row to dict
        profile_dict = dict(profile)

        profile_data = {
            'bot_name': profile_dict['bot_name'] or 'SKAILA Assistant',
            'bot_avatar': profile_dict['bot_avatar'] or '🤖',
            'conversation_style': profile_dict['conversation_style'] or 'friendly',
            'learning_style': profile_dict['learning_preferences'] or 'adaptive',
            'difficulty_preference': profile_dict['difficulty_preference'] or 'medium',
            'conversation_tone': profile_dict['conversation_style'] or 'friendly',
            'strong_subjects': (profile_dict['subject_strengths'] or '').split(',') if profile_dict['subject_strengths'] else [],
            'weak_subjects': (profile_dict['subject_weaknesses'] or '').split(',') if profile_dict['subject_weaknesses'] else [],
            'personality_traits': (profile_dict['personality_traits'] or '').split(',') if profile_dict.get('personality_traits') else [],
            'total_interactions': profile_dict.get('total_interactions', 0),
            'success_rate': profile_dict.get('success_rate', 0.0)
        }

        print(f"🔍 Enhanced AI Profile loaded: {profile_data['bot_name']} (Style: {profile_data['conversation_style']}, Learning: {profile_data['learning_style']})")
        return jsonify(profile_data)

    except Exception as e:
        print(f"❌ Error in /api/ai/profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/profile', methods=['POST'])
def api_save_ai_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        print(f"💾 Saving enhanced AI profile for user {session['user_id']}: {data}")

        conn = get_db_connection()
        conn.execute('''
            INSERT OR REPLACE INTO ai_profiles 
            (utente_id, bot_name, bot_avatar, conversation_style, learning_preferences, 
             difficulty_preference, subject_strengths, subject_weaknesses, personality_traits, 
             preferred_examples, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            session['user_id'],
            data.get('bot_name', 'SKAILA Assistant'),
            data.get('bot_avatar', '🤖'),
            data.get('conversation_tone', 'friendly'),
            data.get('learning_style', 'adaptive'),
            data.get('difficulty_preference', 'medium'),
            ','.join(data.get('strong_subjects', [])),
            ','.join(data.get('weak_subjects', [])),
            ','.join(data.get('personality_traits', [])),
            data.get('preferred_examples', 'mixed')
        ))
        conn.commit()
        conn.close()

        print(f"✅ AI Profile saved successfully for {session.get('nome', 'User')}")
        return jsonify({'success': True, 'message': 'Profilo AI aggiornato con successo!'})

    except Exception as e:
        print(f"❌ Error saving AI profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message.strip():
            return jsonify({'error': 'Messaggio vuoto'}), 400

        print(f"🤖 AI Chat request from {session.get('nome', 'User')}: {message[:50]}...")

        # Carica profilo utente per personalizzazione
        conn = get_db_connection()
        profile = conn.execute('''
            SELECT * FROM ai_profiles WHERE utente_id = ?
        ''', (session['user_id'],)).fetchone()

        profile_dict = dict(profile) if profile else {}

        # Ottimizzazione costi AI
        from ai_cost_manager import optimize_ai_costs, cost_manager

        cached_response, estimated_cost = optimize_ai_costs(
            message, 
            profile_dict, 
            session['user_id']
        )

        if cached_response and estimated_cost == 0.0:
            # Risposta dalla cache
            response = cached_response
            print(f"✅ Cache hit - risposta servita dalla cache")
        else:
            # Genera nuova risposta AI
            response = ai_bot.generate_response(
                message, 
                session['nome'], 
                session['ruolo'],
                session['user_id']
            )

            # Cache la risposta per future richieste
            if ai_bot.openai_available:
                user_context = f"{profile_dict.get('conversation_style', '')}{profile_dict.get('learning_preferences', '')}"
                cost_manager.cache_response(message, response, user_context, 'gpt-3.5-turbo')

                # Traccia il costo se non era cached
                if estimated_cost > 0:
                    input_tokens = cost_manager.estimate_tokens(message)
                    output_tokens = cost_manager.estimate_tokens(response)
                    actual_cost = cost_manager.calculate_cost('gpt-3.5-turbo', input_tokens, output_tokens)
                    cost_manager.track_cost(
                        session['user_id'], 
                        'gpt-3.5-turbo', 
                        input_tokens, 
                        output_tokens, 
                        actual_cost, 
                        'chat'
                    )

        # Analizza il messaggio per insights
        subject_detected = ai_bot.detect_subject(message)
        sentiment_analysis = ','.join(ai_bot.analyze_user_sentiment(message))

        # Salva conversazione AI avanzata nel database
        conn.execute('''
            INSERT INTO ai_conversations 
            (utente_id, message, response, subject_detected, sentiment_analysis, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (session['user_id'], message, response, subject_detected, sentiment_analysis))

        # Aggiorna contatori nel profilo
        conn.execute('''
            UPDATE ai_profiles 
            SET total_interactions = total_interactions + 1,
                last_updated = CURRENT_TIMESTAMP
            WHERE utente_id = ?
        ''', (session['user_id'],))

        conn.commit()
        conn.close()

        # Gamification - Domanda AI
        gamification_result = gamification_system.award_xp(
            session['user_id'], 
            'ai_question', 
            description=f"Domanda AI su {subject_detected}"
        )

        # Aggiorna progresso sfide giornaliere
        gamification_system.update_challenge_progress(session['user_id'], 'ai_questions')

        # Prepara risposta con dati del profilo
        bot_data = {
            'response': response,
            'bot_name': profile_dict.get('bot_name') if profile_dict else 'SKAILA Assistant',
            'bot_avatar': profile_dict.get('bot_avatar') if profile_dict else '🤖',
            'subject_detected': subject_detected,
            'sentiment': sentiment_analysis,
            'personalized': True,
            'openai_powered': ai_bot.openai_available,
            'cached': cached_response is not None and estimated_cost == 0.0
        }

        print(f"✅ AI Response generated (Subject: {subject_detected}, Powered by: {'OpenAI' if ai_bot.openai_available else 'Fallback'})")
        return jsonify(bot_data)

    except Exception as e:
        print(f"❌ Error in enhanced AI chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/usage-stats')
def api_ai_usage_stats():
    """API per statistiche di utilizzo AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        from ai_cost_manager import cost_manager

        stats = cost_manager.get_usage_stats(session['user_id'])
        return jsonify(stats)

    except Exception as e:
        print(f"❌ Error loading AI usage stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/dashboard')
def api_ai_dashboard():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorizzato'}), 401

    try:
        print(f"📊 Loading AI dashboard for user {session.get('nome', 'Unknown')}")
        conn = get_db_connection()

        # Calcola metriche avanzate di progresso
        total_conversations = conn.execute('''
            SELECT COUNT(*) FROM ai_conversations WHERE utente_id = ?
        ''', (session['user_id'],)).fetchone()[0]

        # Analisi per materia
        subject_stats = conn.execute('''
            SELECT subject_detected, COUNT(*) as count
            FROM ai_conversations 
            WHERE utente_id = ? AND subject_detected IS NOT NULL
            GROUP BY subject_detected
            ORDER BY count DESC
        ''', (session['user_id'],)).fetchall()

        # Analisi sentiment nel tempo
        recent_sentiment = conn.execute('''
            SELECT sentiment_analysis, COUNT(*) as count
            FROM ai_conversations 
            WHERE utente_id = ? AND timestamp > datetime('now', '-7 days')
            GROUP BY sentiment_analysis
        ''', (session['user_id'],)).fetchall()

        # Carica profilo per raccomandazioni
        user_profile = ai_bot.load_user_profile(session['user_id'])
        analytics = ai_bot.get_learning_analytics(session['user_id'])

        # Genera raccomandazioni e obiettivi personalizzati
        recommendations = ai_bot.generate_learning_recommendations(session['user_id'], analytics)
        daily_goals = ai_bot.generate_daily_goals(user_profile)

        # Calcola streak e consistenza
        weekly_conversations = conn.execute('''
            SELECT COUNT(*) FROM ai_conversations 
            WHERE utente_id = ? AND timestamp > datetime('now', '-7 days')
        ''', (session['user_id'],)).fetchone()[0]

        dashboard_data = {
            'progress_metrics': {
                'overall_progress': min(total_conversations * 8, 100),
                'weekly_activity': weekly_conversations,
                'consistency': min((weekly_conversations / 7) * 100, 100),
                'total_interactions': total_conversations,
                'study_streak': analytics.get('progress_metrics', {}).get('weekly_activity', 0)
            },
            'subject_analytics': [
                {
                    'name': row[0].title() if row[0] != 'general' else 'Generale',
                    'interactions': row[1],
                    'progress': min(row[1] * 15, 100)
                } for row in subject_stats[:5]
            ],
            'sentiment_trends': [
                {
                    'sentiment': row[0],
                    'frequency': row[1]
                } for row in recent_sentiment
            ],
            'learning_analytics': analytics,
            'achievements': [
                {'name': '🌱 Primi Passi', 'description': 'Prima conversazione AI', 'unlocked': total_conversations > 0, 'progress': 100 if total_conversations > 0 else 0},
                {'name': '💬 Conversatore', 'description': '10 conversazioni completate', 'unlocked': total_conversations >= 10, 'progress': min((total_conversations / 10) * 100, 100)},
                {'name': '🎓 Studioso', 'description': 'Una settimana di studio costante', 'unlocked': weekly_conversations >= 5, 'progress': min((weekly_conversations / 5) * 100, 100)},
                {'name': '🚀 Esperto AI', 'description': '50 conversazioni AI completate', 'unlocked': total_conversations >= 50, 'progress': min((total_conversations / 50) * 100, 100)},
                {'name': '🌟 Master Learner', 'description': 'Padronanza in 3+ materie', 'unlocked': len(subject_stats) >= 3, 'progress': min((len(subject_stats) / 3) * 100, 100)}
            ],
            'recommendations': recommendations[:5],  # Top 5 raccomandazioni
            'daily_goals': daily_goals,
            'personalization_score': min((len(user_profile.get('subject_strengths', [])) + len(user_profile.get('subject_weaknesses', []))) * 25, 100),
            'bot_personality': {
                'name': user_profile.get('bot_name', 'SKAILA Assistant'),
                'avatar': user_profile.get('bot_avatar', '🤖'),
                'style': user_profile.get('conversation_style', 'friendly'),
                'learning_approach': user_profile.get('learning_preferences', 'adaptive')
            }
        }

        conn.close()
        print(f"✅ AI Dashboard loaded with {total_conversations} interactions, {len(subject_stats)} subjects")
        return jsonify(dashboard_data)

    except Exception as e:
        print(f"❌ Error in enhanced AI dashboard: {e}")
        return jsonify({'error': str(e)}), 500

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

@socketio.on('join_conversation')
def handle_join_conversation(data):
    if 'user_id' not in session:
        return

    conversation_id = data['conversation_id']
    join_room(f"chat_{conversation_id}")

    emit('joined_conversation', {
        'conversation_id': conversation_id
    })

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return

    conversation_id = data['conversation_id']
    contenuto = data.get('contenuto', '')

    if not contenuto.strip():
        return

    # Salva messaggio nel database
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO messaggi (chat_id, utente_id, contenuto)
        VALUES (?, ?, ?)
    ''', (conversation_id, session['user_id'], contenuto))

    message_id = cursor.lastrowid
    conn.commit()

    # Ottieni il messaggio appena inserito con i dati utente
    messaggio = conn.execute('''
        SELECT m.*, u.nome, u.cognome, u.username, u.ruolo,
               m.timestamp as data_invio
        FROM messaggi m
        JOIN utenti u ON m.utente_id = u.id
        WHERE m.id = ?
    ''', (message_id,)).fetchone()
    conn.close()

    # Gamification - Messaggio inviato
    gamification_system.award_xp(session['user_id'], 'message_sent', description="Messaggio in chat")
    gamification_system.update_challenge_progress(session['user_id'], 'messages')

    # Invia a tutti nella chat
    emit('new_message', dict(messaggio), room=f"chat_{conversation_id}")

@socketio.on('typing_start')
def handle_typing_start(data):
    if 'user_id' not in session:
        return

    conversation_id = data['conversation_id']
    emit('user_typing', {
        'conversation_id': conversation_id,
        'user_name': session['nome'],
        'typing': True
    }, room=f"chat_{conversation_id}", include_self=False)

@socketio.on('typing_stop')
def handle_typing_stop(data):
    if 'user_id' not in session:
        return

    conversation_id = data['conversation_id']
    emit('user_typing', {
        'conversation_id': conversation_id,
        'user_name': session['nome'],
        'typing': False
    }, room=f"chat_{conversation_id}", include_self=False)

def reset_database():
    """Forza la ricreazione completa del database - Solo per manutenzione"""
    import os
    if os.path.exists('skaila.db'):
        os.remove('skaila.db')
        print("🗑️ Database rimosso")
    init_db()
    print("🔄 Database ricreato completamente")

if __name__ == '__main__':
    # Inizializza database solo se non esiste
    if not os.path.exists('skaila.db'):
        print("🔧 Creazione database iniziale...")
        init_db()
    else:
        print("✅ Database esistente trovato - riutilizzo")

    # Usa porta fissa per development
    port = int(os.environ.get('PORT', 5000))

    print(f"🚀 SKAILA Server starting on port {port}")
    print(f"🌐 URL: http://0.0.0.0:{port}")

    # Modalità production per migliore performance
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)