# -*- coding: utf-8 -*-
"""
SKAILA - Main Application
Applicazione Flask modulare e scalabile
"""

import os
import time
from datetime import timedelta
from flask import Flask, render_template, redirect, session, make_response, request
from flask_socketio import SocketIO

# Import moduli personalizzati
from database_manager import db_manager
from environment_manager import env_manager
from performance_cache import (
    user_cache, chat_cache, message_cache, ai_cache, gamification_cache,
    cache_user_data, get_cached_user, cache_chat_messages, get_cached_chat_messages,
    invalidate_user_cache, get_cache_health
)
from production_monitor import production_monitor, monitor_request
from school_system import school_system
from gamification import gamification_system
from ai_chatbot import AISkailaBot

# Import routes modulari
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
from routes.school_routes import school_bp
from routes.credits_routes import credits_bp
from routes.socket_routes import register_socket_events

# Import services
from services.auth_service import auth_service
from services.user_service import user_service

class SkailaApp:
    """Classe principale per l'applicazione SKAILA"""

    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = None
        self.ai_bot = None
        self.setup_app()
        self.register_routes()
        self.setup_socketio()
        self.init_systems()

    def setup_app(self):
        """Configurazione base Flask con gestione sicura environment"""
        # Usa environment manager per configurazione sicura
        flask_config = env_manager.get_flask_config()
        self.app.config.update(flask_config)
        
        # Sessioni permanenti
        self.app.permanent_session_lifetime = timedelta(days=30)
        
        # Status info per monitoring
        print(f"🔐 Environment: {'Production' if env_manager.is_production() else 'Development'}")
        ai_status = env_manager.get_ai_status()
        db_status = env_manager.get_database_status()
        print(f"🤖 AI Mode: {ai_status['mode']}")
        print(f"🗄️ Database: {db_status['primary']}")

        # Headers per Replit e sicurezza produzione
        @self.app.after_request
        def after_request(response):
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.replit.com *.repl.co"
            
            # CORS sicuro: restrictive in produzione, permissive in development
            if self.app.debug:
                response.headers['Access-Control-Allow-Origin'] = '*'
            else:
                # Produzione: limita origini consentite (no ACAO se origin non allowed)
                allowed_origins = env_manager.get_allowed_origins()
                origin = request.headers.get('Origin', '')
                if origin and any(origin.endswith(allowed.strip()) for allowed in allowed_origins):
                    response.headers['Access-Control-Allow-Origin'] = origin
                # Non impostare ACAO se origin non allowed (più sicuro di "null")
                    
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRF-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'

            # Cache control per development
            if self.app.debug:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'

            return response

    def register_routes(self):
        """Registra tutti i blueprint delle routes"""

        # Route principali
        @self.app.route('/')
        def index():
            if 'user_id' in session:
                return redirect('/dashboard')
            return render_template('index.html')

        @self.app.route('/chat')
        def chat():
            if 'user_id' not in session:
                return redirect('/login')

            with db_manager.get_connection() as conn:
                if session['ruolo'] == 'admin':
                    chats = conn.execute('SELECT * FROM chat ORDER BY nome').fetchall()
                else:
                    chats = conn.execute('''
                        SELECT c.* FROM chat c
                        JOIN partecipanti_chat pc ON c.id = pc.chat_id
                        WHERE pc.utente_id = ? OR c.classe = ?
                        ORDER BY c.nome
                    ''', (session['user_id'], session.get('classe', ''))).fetchall()

                utenti_online = user_service.get_online_users(session['user_id'])

            return render_template('chat.html', 
                                 user=session, 
                                 chats=chats, 
                                 utenti_online=utenti_online)

        @self.app.route('/ai-chat')
        def ai_chat():
            if 'user_id' not in session:
                return redirect('/login')
            return render_template('ai_chat.html', user=session)

        @self.app.route('/gamification')
        def gamification_dashboard():
            if 'user_id' not in session:
                return redirect('/login')

            response = make_response(render_template('gamification_dashboard.html', user=session))
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
            return response

        # Registra blueprints
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(dashboard_bp)
        self.app.register_blueprint(api_bp)
        self.app.register_blueprint(school_bp)
        self.app.register_blueprint(credits_bp)
        
        # Aggiungi CSRF protection context processor
        from csrf_protection import inject_csrf_token
        self.app.context_processor(inject_csrf_token)

    def setup_socketio(self):
        """Configurazione Socket.IO"""
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
            allow_upgrades=True,
            transports=['websocket', 'polling'],
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25,
            max_http_buffer_size=1000000
        )

        # Registra eventi Socket.IO
        register_socket_events(self.socketio)

    def init_systems(self):
        """Inizializza sistemi ausiliari"""
        # Inizializza AI Bot
        self.ai_bot = AISkailaBot()

        # Inizializza gamification
        gamification_system.init_gamification_tables()

        # Crea indici database ottimizzati
        db_manager.create_optimized_indexes()

        # Inizializza database se necessario
        self.init_database()

    def init_database(self):
        """Inizializzazione database con dati demo"""
        if db_manager.db_type == 'postgresql':
            # Per PostgreSQL, verifica se le tabelle esistono
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'utenti'")
                    table_exists = cursor.fetchone()[0] > 0

                    if not table_exists:
                        print("🔧 Creazione schema PostgreSQL...")
                        self.create_database_schema()
                        self.create_demo_data()
                    else:
                        print("✅ Database PostgreSQL esistente trovato")
            except Exception as e:
                print(f"🔧 Inizializzazione database PostgreSQL: {e}")
                self.create_database_schema()
                self.create_demo_data()
        else:
            # Per SQLite, controllo file
            if not os.path.exists('skaila.db'):
                print("🔧 Creazione database SQLite iniziale...")
                self.create_database_schema()
                self.create_demo_data()
            else:
                print("✅ Database SQLite esistente trovato")

    def create_database_schema(self):
        """Crea schema database"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Tabella utenti - compatibile PostgreSQL/SQLite
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS utenti (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        nome TEXT NOT NULL,
                        cognome TEXT NOT NULL,
                        classe TEXT,
                        ruolo TEXT DEFAULT 'studente',
                        attivo BOOLEAN DEFAULT TRUE,
                        primo_accesso BOOLEAN DEFAULT TRUE,
                        ultimo_accesso TIMESTAMP,
                        status_online BOOLEAN DEFAULT FALSE,
                        avatar TEXT DEFAULT 'default.jpg',
                        data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                cursor.execute('''
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

            # Tabelle chat
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat (
                        id SERIAL PRIMARY KEY,
                        nome TEXT NOT NULL,
                        descrizione TEXT,
                        tipo TEXT DEFAULT 'classe',
                        classe TEXT,
                        privata BOOLEAN DEFAULT FALSE,
                        creatore_id INTEGER,
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (creatore_id) REFERENCES utenti (id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messaggi (
                        id SERIAL PRIMARY KEY,
                        chat_id INTEGER,
                        utente_id INTEGER,
                        contenuto TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tipo TEXT DEFAULT 'testo',
                        file_allegato TEXT,
                        modificato BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (chat_id) REFERENCES chat (id),
                        FOREIGN KEY (utente_id) REFERENCES utenti (id)
                    )
                ''')

                cursor.execute('''
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

                # Tabelle AI
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_profiles (
                        id SERIAL PRIMARY KEY,
                        utente_id INTEGER UNIQUE,
                        bot_name TEXT DEFAULT 'SKAILA Assistant',
                        bot_avatar TEXT DEFAULT 'bot',
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

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_conversations (
                        id SERIAL PRIMARY KEY,
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
                        follow_up_needed BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (utente_id) REFERENCES utenti (id)
                    )
                ''')
            else:
                # SQLite schema (original)
                cursor.execute('''
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

                cursor.execute('''
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

                cursor.execute('''
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

                cursor.execute('''
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

                cursor.execute('''
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

    def create_demo_data(self):
        """Crea dati demo per testing"""
        with db_manager.get_connection() as conn:
            # Verifica se esistono già utenti admin
            admin_exists = conn.execute('SELECT COUNT(*) FROM utenti WHERE ruolo = "admin"').fetchone()[0]

            if admin_exists == 0:
                print("🔧 Creazione utenti demo...")

                # Crea utenti demo con password sicure
                demo_users = [
                    ('admin', 'admin@skaila.it', 'admin123', 'Admin', 'SKAILA', '', 'admin'),
                    ('founder', 'founder@skaila.it', 'founder123', 'Daniele', 'Founder', '', 'admin'),
                    ('papa', 'papa@skaila.it', 'papa123', 'Papà', 'Famiglia', '', 'genitore'),
                    ('mamma', 'mamma@skaila.it', 'mamma123', 'Mamma', 'Famiglia', '', 'genitore'),
                    ('alice_demo', 'alice@test.skaila.it', 'test123', 'Alice', 'Demo', '3A', 'studente'),
                    ('prof_demo', 'prof@test.skaila.it', 'prof123', 'Prof', 'Demo', '3A', 'professore'),
                ]

                for username, email, password, nome, cognome, classe, ruolo in demo_users:
                    password_hash = auth_service.hash_password(password)

                    conn.execute('''
                        INSERT OR REPLACE INTO utenti 
                        (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    ''', (username, email, password_hash, nome, cognome, classe, ruolo))

                # Crea chat demo
                chat_rooms = [
                    ('💬 Chat Generale SKAILA', 'Chat generale per tutti gli utenti', 'generale', ''),
                    ('📚 Aiuto Compiti', 'Chat per ricevere e dare aiuto con i compiti', 'tematica', ''),
                    ('💻 Informatica & Coding', 'Discussioni su programmazione e tecnologia', 'tematica', ''),
                    ('🧮 Matematica & Fisica', 'Gruppo di studio per materie scientifiche', 'tematica', ''),
                    ('Chat Classe 3A', 'Chat generale per la classe 3A', 'classe', '3A'),
                ]

                for nome, descrizione, tipo, classe in chat_rooms:
                    conn.execute('''
                        INSERT OR IGNORE INTO chat (nome, descrizione, tipo, classe)
                        VALUES (?, ?, ?, ?)
                    ''', (nome, descrizione, tipo, classe))

                print("✅ Dati demo creati con successo")

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Avvia l'applicazione"""
        print(f"🚀 SKAILA Server starting on port {port}")
        print(f"🌐 URL: http://{host}:{port}")
        print(f"📊 Database: {db_manager.db_type}")
        print(f"🤖 AI Bot: {'✅ Attivo' if self.ai_bot.openai_available else '⚠️ Mock mode'}")

        self.socketio.run(
            self.app, 
            host=host, 
            port=port, 
            debug=debug, 
            allow_unsafe_werkzeug=True
        )

# Inizializzazione e avvio applicazione
def create_app():
    """Factory per creare l'app"""
    return SkailaApp()

if __name__ == '__main__':
    # Crea e avvia applicazione
    skaila_app = create_app()

    # Porta da environment o default
    port = int(os.environ.get('PORT', 5000))

    # Avvia in modalità production
    skaila_app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False
    )