# -*- coding: utf-8 -*-
"""
SKAILA - Main Application
Applicazione Flask modulare e scalabile
"""

import os
import time
import threading  # Import threading for the keep-alive thread
from datetime import timedelta
from flask import Flask, render_template, redirect, session, make_response, request, g, flash
from flask_socketio import SocketIO
from flask_compress import Compress

# Import moduli personalizzati
from services.database.database_manager import db_manager
from services.utils.environment_manager import env_manager
from services.monitoring.performance_cache import (
    user_cache, chat_cache, message_cache, ai_cache, gamification_cache,
    cache_user_data, get_cached_user, cache_chat_messages, get_cached_chat_messages,
    invalidate_user_cache, get_cache_health
)
# New structured monitoring system
from services.monitoring_service import (
    ProductionLogger, MetricsCollector, PerformanceMonitor,
    RequestMonitor, DatabaseMonitor
)
from services.school.school_system import school_system
from services.gamification.gamification import gamification_system
from services.ai.ai_chatbot import AISkailaBot
from services.reports.report_scheduler import ReportScheduler
from services.calendar.calendar_system import calendar_system
from services.telemetry.telemetry_engine import telemetry_engine

# Import routes modulari
from routes.auth_routes import auth_bp
from routes.api_auth_routes import api_auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
from routes.school_routes import school_bp
from routes.credits_routes import credits_bp
from routes.admin_school_codes_routes import admin_codes_bp
from routes.messaging_routes import messaging_bp
from routes.messaging_api import messaging_api_bp
from routes.ai_chat_routes import ai_chat_bp
from routes.socket_routes import register_socket_events
from routes.admin_calendar_routes import admin_calendar_bp
from routes.admin_reports_routes import admin_reports_bp
from routes.documentation_routes import documentation_bp
from routes.skaila_connect_routes import skaila_connect_bp
from routes.bi_dashboard_routes import bi_bp # BI Dashboard Blueprint
from routes.timer_routes import timer_bp # Study Timer
from routes.online_users_routes import online_users_bp # Online Users API
from routes.cyberpunk_presence_routes import cyberpunk_presence_bp # Cyberpunk Presence Demo
from routes.calendar_routes import smart_calendar_bp # Smart Calendar System
from routes.telemetry_routes import telemetry_bp # Behavioral Telemetry System
from routes.early_warning_routes import early_warning_bp # Early Warning Dashboard
from routes.portfolio_routes import portfolio_bp # Student Portfolio & Candidate Cards
from routes.opportunities_api import opportunities_api_bp # Opportunities One-Click Apply API
from routes.pcto_routes import pcto_bp # PCTO Tracker & Digital Logbook
from routes.parent_routes import parent_bp # Parent Dashboard - Zero-Friction Child Monitoring
from routes.gamification_api_v2 import gamification_api_bp # Advanced Gamification API V2

# Import services
from services.auth_service import auth_service
from services.user_service import user_service

# Import API documentation
from docs.api_documentation import init_swagger

# Import structured logging
from shared.logging.structured_logger import auth_logger, api_logger

class SkailaApp:
    """Classe principale per l'applicazione SKAILA"""

    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = None
        self.ai_bot = None

        # Initialize new monitoring system (delayed to avoid blocking during eventlet init)
        self.production_logger = None
        self.metrics_collector = None
        self.performance_monitor = None

        # Track initialization state for readiness checks
        self._systems_initialized = False
        
        self.setup_app()
        self.register_routes()
        self.setup_socketio()
        self.init_systems()
        self.init_monitoring_delayed()
        
        # Store reference for health checks
        self.app.config['SKAILA_APP'] = self

    def setup_app(self):
        """Configurazione base Flask con gestione sicura environment"""
        # Usa environment manager per configurazione sicura
        flask_config = env_manager.get_flask_config()
        self.app.config.update(flask_config)

        # Abilita compressione response
        Compress(self.app)
        
        # Initialize Swagger API documentation
        init_swagger(self.app)
        print("📚 API Documentation available at /api/docs")
        api_logger.info("Swagger API documentation initialized", endpoint="/api/docs")

        # Sessioni permanenti
        self.app.permanent_session_lifetime = timedelta(days=30)

        # Status info per monitoring
        is_prod = env_manager.is_production()
        print(f"🔐 Environment: {'Production' if is_prod else 'Development'}")
        ai_status = env_manager.get_ai_status()
        db_status = env_manager.get_database_status()
        print(f"🤖 AI Mode: {ai_status['mode']}")
        print(f"🗄️ Database: {db_status['primary']}")
        
        # Structured logging for startup
        api_logger.info("SKAILA application startup", 
                       environment="production" if is_prod else "development",
                       ai_mode=ai_status['mode'],
                       database=db_status['primary'])

        # TEMPORARILY DISABLED - Request monitoring hooks causing eventlet mainloop blocking
        # Will re-enable after implementing proper eventlet-compatible monitoring
        # @self.app.before_request
        # def before_request():
        #     pass  # Monitoring temporarily disabled

        # @self.app.after_request
        # def after_request(response):
        #     pass  # Monitoring temporarily disabled

        # Headers per Replit e sicurezza produzione
        @self.app.after_request
        def after_request_headers(response):
            # Security Headers (OWASP Best Practices)
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

            # HSTS (solo in produzione)
            if not env_manager.is_development():
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

            # CSP (Content Security Policy)
            response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.replit.com *.repl.co"

            # CORS sicuro: restrictive in produzione, permissive in development
            if env_manager.is_development():
                response.headers['Access-Control-Allow-Origin'] = '*'
            else:
                # Produzione: limita origini consentite (no ACAO se origin non allowed)
                allowed_origins = env_manager.get_allowed_origins()
                origin = request.headers.get('Origin', '')
                if origin and self._is_origin_allowed(origin, allowed_origins):
                    response.headers['Access-Control-Allow-Origin'] = origin
                # Non impostare ACAO se origin non allowed (più sicuro di "null")

            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRF-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'

            # Cache control per development
            if env_manager.is_development():
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'

            return response

    def register_routes(self):
        """Registra tutti i blueprint delle routes"""

        # Before request: controlla scadenza sessioni brevi (senza remember_me)
        @self.app.before_request
        def check_session_expiry():
            """Controlla scadenza sessioni senza remember_me"""
            if 'user_id' in session and 'session_expires' in session:
                from datetime import datetime
                try:
                    expires = datetime.fromisoformat(session['session_expires'])
                    if datetime.utcnow() > expires:
                        print(f"⏰ Sessione scaduta per user {session.get('user_id')}")
                        session.clear()
                        flash('⏰ Sessione scaduta. Effettua nuovamente il login.', 'info')
                        return redirect('/login')
                except (ValueError, TypeError):
                    pass  # Timestamp invalido, ignora

        # Route principali
        @self.app.route('/', methods=['GET', 'HEAD'])
        def index():
            # Fast path for health check probes (Autoscale, load balancers)
            # Detect HEAD requests or specific User-Agents used by health checkers
            if request.method == 'HEAD' or \
               'GoogleHC' in request.headers.get('User-Agent', '') or \
               'kube-probe' in request.headers.get('User-Agent', '') or \
               'Replit' in request.headers.get('User-Agent', ''):
                return '', 200
            
            if 'user_id' in session:
                return redirect('/dashboard')
            
            # Statistiche pubbliche per la homepage
            try:
                total_users = db_manager.query('''
                    SELECT COUNT(*) as count FROM utenti WHERE attivo = true
                ''', one=True)
                
                total_schools = db_manager.query('''
                    SELECT COUNT(*) as count FROM scuole WHERE attiva = true
                ''', one=True)
                
                total_students = db_manager.query('''
                    SELECT COUNT(*) as count FROM utenti WHERE ruolo = 'studente' AND attivo = true
                ''', one=True)
                
                ai_interactions = db_manager.query('''
                    SELECT COUNT(*) as count FROM ai_conversations
                ''', one=True)
                
                stats = {
                    'total_users': total_users['count'] if total_users else 0,
                    'total_schools': total_schools['count'] if total_schools else 0,
                    'total_students': total_students['count'] if total_students else 0,
                    'ai_interactions': ai_interactions['count'] if ai_interactions else 0
                }
            except Exception as e:
                print(f"Error loading homepage stats: {e}")
                stats = {
                    'total_users': 0,
                    'total_schools': 0,
                    'total_students': 0,
                    'ai_interactions': 0
                }
            
            return render_template('index.html', stats=stats)

        @self.app.route('/chat')
        def chat():
            if 'user_id' not in session:
                return redirect('/login')

            # Usa db_manager.query per query parametrizzate sicure PostgreSQL
            if session['ruolo'] == 'admin':
                chats = db_manager.query('SELECT * FROM chat ORDER BY nome') or []
            else:
                chats = db_manager.query('''
                    SELECT c.* FROM chat c
                    JOIN partecipanti_chat pc ON c.id = pc.chat_id
                    WHERE pc.utente_id = %s OR c.classe = %s
                    ORDER BY c.nome
                ''', (session['user_id'], session.get('classe', ''))) or []

            utenti_online = user_service.get_online_users(session['user_id'])

            # Usa il nuovo template moderno
            return render_template('chat_modern.html',
                                 user=session,
                                 chats=chats,
                                 utenti_online=utenti_online)

        @self.app.route('/ai-chat')
        def ai_chat():
            if 'user_id' not in session:
                return redirect('/login')
            return render_template('ai_coach_modern.html', user=session)

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
        self.app.register_blueprint(api_auth_bp)
        self.app.register_blueprint(dashboard_bp)
        self.app.register_blueprint(api_bp)
        self.app.register_blueprint(school_bp)
        self.app.register_blueprint(credits_bp)
        self.app.register_blueprint(admin_codes_bp)
        self.app.register_blueprint(messaging_bp)
        self.app.register_blueprint(messaging_api_bp)
        self.app.register_blueprint(ai_chat_bp)
        self.app.register_blueprint(skaila_connect_bp)  # SKAILA Connect - Alternanza Scuola-Lavoro
        self.app.register_blueprint(admin_calendar_bp)  # Dashboard Admin + Calendario
        self.app.register_blueprint(admin_reports_bp)  # Report Automatici
        self.app.register_blueprint(bi_bp) # BI Dashboard Blueprint
        self.app.register_blueprint(timer_bp) # Study Timer
        self.app.register_blueprint(online_users_bp) # Online Users API for circulating avatars
        self.app.register_blueprint(cyberpunk_presence_bp) # Cyberpunk Presence Demo
        self.app.register_blueprint(smart_calendar_bp) # Smart Calendar System
        self.app.register_blueprint(telemetry_bp) # Behavioral Telemetry System
        self.app.register_blueprint(early_warning_bp) # Early Warning Dashboard
        self.app.register_blueprint(portfolio_bp) # Student Portfolio API
        self.app.register_blueprint(opportunities_api_bp) # Opportunities Marketplace API
        self.app.register_blueprint(pcto_bp) # PCTO Tracker & Digital Logbook
        self.app.register_blueprint(parent_bp) # Parent Dashboard - Child Monitoring
        self.app.register_blueprint(gamification_api_bp) # Advanced Gamification V2

        # Demo routes sicure (solo dati mock)
        from routes.demo_routes import demo_bp
        self.app.register_blueprint(demo_bp)

        # Registro Elettronico API
        from routes.registro_routes import registro_bp
        self.app.register_blueprint(registro_bp)

        # Production monitoring routes
        from routes.monitoring_routes import monitoring_bp
        self.app.register_blueprint(monitoring_bp)
        
        # Health check endpoints (lightweight, for Autoscale)
        from routes.health_routes import health_bp
        self.app.register_blueprint(health_bp)

        # Registra blueprint documentazione
        self.app.register_blueprint(documentation_bp)

        # Admin Features Management
        from routes.admin_features_routes import admin_features_bp
        self.app.register_blueprint(admin_features_bp)

        # 🔒 SECURITY: Initialize global security middlewares
        self._init_security_middlewares()

        # Error handlers personalizzati
        @self.app.errorhandler(404)
        def page_not_found(e):
            return render_template('404.html'), 404

        @self.app.errorhandler(500)
        def internal_server_error(e):
            return render_template('500.html'), 500

    def setup_socketio(self):
        """Configurazione Socket.IO con CORS sicuro"""
        # CORS Socket.IO: restrictive in produzione, permissive in development
        if env_manager.is_development():
            cors_origins = "*"
        else:
            # Produzione: usa le stesse origini allowed del CORS HTTP
            allowed_origins = env_manager.get_allowed_origins()
            cors_origins = self._generate_socketio_cors_origins(allowed_origins)

        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins=cors_origins,
            logger=False,
            engineio_logger=False,
            allow_upgrades=True,
            transports=['websocket', 'polling'],
            async_mode='eventlet',  # Eventlet per compatibilità con worker Gunicorn
            ping_timeout=60,
            ping_interval=25,
            max_http_buffer_size=1000000
        )

        # Registra eventi Socket.IO
        register_socket_events(self.socketio)

    def _is_origin_allowed(self, origin: str, allowed_origins: list) -> bool:
        """Verifica se un'origine è consentita con supporto wildcard"""
        for allowed in allowed_origins:
            allowed = allowed.strip()

            # Pattern wildcard (es: *.replit.com)
            if allowed.startswith('*.'):
                domain = allowed[2:]  # Rimuovi '*.' dall'inizio
                # Controlla se l'origine termina con .domain o è esattamente domain
                if origin.endswith(f'.{domain}') or origin.endswith(f'://{domain}'):
                    return True
            # Match esatto
            elif origin.endswith(f'://{allowed}'):
                return True

        return False

    def _generate_socketio_cors_origins(self, allowed_origins: list) -> list:
        """Genera pattern CORS validi per Socket.IO"""
        cors_origins = []

        for origin in allowed_origins:
            origin = origin.strip()

            # Normalizza pattern wildcard
            if origin.startswith('*.'):
                base_domain = origin[2:]  # Rimuovi '*.' dall'inizio
                # Aggiungi pattern per subdomini e dominio principale
                cors_origins.extend([
                    f'https://{base_domain}',      # Match esatto
                    f'https://*.{base_domain}',    # Match subdomini
                    f'http://{base_domain}',       # HTTP fallback per development
                    f'http://*.{base_domain}'      # HTTP subdomini fallback
                ])
            else:
                # Pattern esatto senza wildcard
                cors_origins.extend([
                    f'https://{origin}',
                    f'http://{origin}'  # HTTP fallback
                ])

        return cors_origins

    def _init_security_middlewares(self):
        """🔒 Initialize all security middlewares (CSRF, Tenant Isolation)"""
        # CSRF Protection Middleware
        from shared.middleware.csrf_middleware import init_csrf_protection
        init_csrf_protection(self.app)
        
        # Tenant Isolation Middleware
        from shared.middleware.tenant_guard import init_tenant_guard
        init_tenant_guard(self.app)
        
        print("🔒 Security middlewares initialized (CSRF + Tenant Isolation)")

    def init_systems(self):
        """Inizializza sistemi ausiliari - deferred to background thread for fast startup"""
        # Inizializza AI Bot (lightweight, no DB)
        self.ai_bot = AISkailaBot()
        
        # Mark as ready for basic health checks immediately
        self._systems_initialized = False
        
        # Start background initialization thread
        def _background_init():
            """Heavy initialization in background after server starts"""
            try:
                # CRITICO: Inizializza sistema scuole multi-tenant
                school_system.init_school_tables()

                # Avvia keep-alive database per evitare Neon sleep
                if db_manager.db_type == 'postgresql':
                    from database_keep_alive import keep_alive
                    keep_alive.start()  # Avvia keep-alive service

                # Inizializza gamification (base + advanced v2)
                gamification_system.init_gamification_tables()
                
                # Inizializza Advanced Gamification V2 (ranks, battle pass, challenges, kudos)
                from services.gamification.advanced_gamification import advanced_gamification
                if advanced_gamification.init_advanced_tables():
                    advanced_gamification.seed_default_badges()
                    advanced_gamification.seed_default_challenges()
                    advanced_gamification.seed_default_powerups()
                    print("🎮 Advanced Gamification V2 initialized")
                
                # Inizializza calendario smart
                calendar_system.init_calendar_tables()

                # Crea indici database ottimizzati
                db_manager.create_optimized_indexes()

                # Inizializza scheduler report automatici (con app context)
                try:
                    with self.app.app_context():
                        self.report_scheduler = ReportScheduler(app=self.app)
                        self.report_scheduler.start()
                except Exception as e:
                    print(f"⚠️ Report scheduler non avviato: {e}")

                # Inizializza database se necessario
                self.init_database()
                
                self._systems_initialized = True
            except Exception as e:
                print(f"⚠️ Background init error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start initialization in background thread after a short delay
        # This allows the server to start accepting connections first
        init_thread = threading.Thread(target=_background_init, daemon=True)
        init_thread.start()

    def init_monitoring_delayed(self):
        """TEMPORARILY DISABLED - Monitoring system causing eventlet mainloop blocking"""
        print("⚠️ Monitoring system temporarily disabled to fix eventlet mainloop blocking")
        # Will re-enable after implementing proper eventlet-compatible monitoring
        # try:
        #     self.production_logger = ProductionLogger()
        #     self.metrics_collector = MetricsCollector()
        #     self.performance_monitor = PerformanceMonitor(
        #         self.metrics_collector, self.production_logger
        #     )
        #     print("✅ New monitoring system initialized successfully")
        # except Exception as e:
        #     print(f"⚠️ Monitoring system initialization failed: {e}")
        #     # Continue without monitoring rather than failing

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
                        # CRITICAL FIX: Verifica sempre se esistono utenti demo
                        cursor.execute("SELECT COUNT(*) FROM utenti WHERE ruolo = 'admin'")
                        admin_exists = cursor.fetchone()[0]
                        if admin_exists == 0:
                            print("⚠️ Nessun admin trovato - creazione account demo...")
                            self.create_demo_data()
                        else:
                            print(f"✅ {admin_exists} account admin esistenti")
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
            cursor = conn.cursor()
            # Verifica se esistono già utenti admin
            if db_manager.db_type == 'postgresql':
                cursor.execute("SELECT COUNT(*) FROM utenti WHERE ruolo = 'admin'")
            else:
                cursor.execute('SELECT COUNT(*) FROM utenti WHERE ruolo = "admin"')
            admin_exists = cursor.fetchone()[0]

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

                    if db_manager.db_type == 'postgresql':
                        # CRITICAL FIX: Usa ON CONFLICT per email (non username) perché email è UNIQUE
                        cursor.execute('''
                            INSERT INTO utenti
                            (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso, attivo)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, false, true)
                            ON CONFLICT (email) DO UPDATE SET
                                password_hash = EXCLUDED.password_hash,
                                attivo = true
                        ''', (username, email, password_hash, nome, cognome, classe, ruolo))
                        print(f"✅ Account demo creato/aggiornato: {email}")
                    else:
                        cursor.execute('''
                            INSERT OR REPLACE INTO utenti
                            (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso, attivo)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 1)
                        ''', (username, email, password_hash, nome, cognome, classe, ruolo))
                        print(f"✅ Account demo creato: {email}")

                # Crea chat demo
                chat_rooms = [
                    ('💬 Chat Generale SKAILA', 'Chat generale per tutti gli utenti', 'generale', ''),
                    ('📚 Aiuto Compiti', 'Chat per ricevere e dare aiuto con i compiti', 'tematica', ''),
                    ('💻 Informatica & Coding', 'Discussioni su programmazione e tecnologia', 'tematica', ''),
                    ('🧮 Matematica & Fisica', 'Gruppo di studio per materie scientifiche', 'tematica', ''),
                    ('Chat Classe 3A', 'Chat generale per la classe 3A', 'classe', '3A'),
                ]

                for nome, descrizione, tipo, classe in chat_rooms:
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('''
                            INSERT INTO chat (nome, descrizione, tipo, classe, attiva)
                            VALUES (%s, %s, %s, %s, true)
                            ON CONFLICT (nome) DO NOTHING
                        ''', (nome, descrizione, tipo, classe))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO chat (nome, descrizione, tipo, classe)
                            VALUES (%s, %s, %s, %s)
                        ''', (nome, descrizione, tipo, classe))

                conn.commit()
                print("✅ Dati demo creati con successo")

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Avvia l'applicazione"""
        print(f"🚀 SKAILA Server starting on port {port}")
        print(f"🌐 URL: http://{host}:{port}")
        print(f"📊 Database: {db_manager.db_type}")
        
        # Safe check for AI bot status
        ai_status = '⚠️ Mock mode'
        if self.ai_bot and hasattr(self.ai_bot, 'openai_available'):
            ai_status = '✅ Attivo' if self.ai_bot.openai_available else '⚠️ Mock mode'
        print(f"🤖 AI Bot: {ai_status}")

        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            log_output=not debug
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