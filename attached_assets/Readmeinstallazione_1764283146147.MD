{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\froman\fcharset0 Times-Bold;\f1\froman\fcharset0 Times-Roman;\f2\fmodern\fcharset0 Courier;
\f3\fmodern\fcharset0 Courier-Bold;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;\red109\green109\blue109;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;\cssrgb\c50196\c50196\c50196;}
{\*\listtable{\list\listtemplateid1\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat1\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid1\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid1}
{\list\listtemplateid2\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat1\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid101\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid2}}
{\*\listoverridetable{\listoverride\listid1\listoverridecount0\ls1}{\listoverride\listid2\listoverridecount0\ls2}}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\sa321\partightenfactor0

\f0\b\fs48 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 \uc0\u55356 \u57262  SISTEMA GAMIFICATION SKAILA - COMPLETO\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Sistema di gamification completo per piattaforma edtech Skaila, progettato per studenti scuole medie (11-14 anni).\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55357 \u56550  CONTENUTO PACCHETTO\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 skaila_gamification/\
\uc0\u9500 \u9472 \u9472  models/\
\uc0\u9474    \u9492 \u9472 \u9472  gamification_models.py       # Modelli SQLAlchemy completi\
\uc0\u9500 \u9472 \u9472  services/\
\uc0\u9474    \u9500 \u9472 \u9472  xp_manager.py                # Gestione XP e livelli\
\uc0\u9474    \u9492 \u9472 \u9472  challenge_manager.py         # Gestione sfide\
\uc0\u9500 \u9472 \u9472  routes/\
\uc0\u9474    \u9492 \u9472 \u9472  gamification_routes.py      # API Flask endpoints\
\uc0\u9500 \u9472 \u9472  migrations/\
\uc0\u9474    \u9492 \u9472 \u9472  001_create_tables.sql       # Migration PostgreSQL\
\uc0\u9500 \u9472 \u9472  templates/                        # (da creare)\
\uc0\u9500 \u9472 \u9472  static/                           # (da creare)\
\uc0\u9492 \u9472 \u9472  utils/                            # (da creare)\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55357 \u56960  INSTALLAZIONE\
\pard\pardeftab720\sa280\partightenfactor0

\fs28 \cf0 1. Setup Database\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Esegui la migration SQL sul tuo database PostgreSQL (Neon):\
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 psql -h <your-neon-host> -U <username> -d <database> -f migrations/001_create_gamification_tables.sql\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 2. Integrazione nel tuo progetto Flask\
\pard\pardeftab720\sa240\partightenfactor0

\fs24 \cf0 A. Copia i file nella tua app:
\f1\b0 \
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 # Nella root del tuo progetto Replit\
cp -r skaila_gamification/models/* app/models/\
cp -r skaila_gamification/services/* app/services/\
cp -r skaila_gamification/routes/* app/routes/\
\pard\pardeftab720\sa240\partightenfactor0

\f0\b\fs24 \cf0 B. Registra il Blueprint in 
\f3\fs26 app.py
\f0\fs24  o 
\f3\fs26 main.py
\f0\fs24 :
\f1\b0 \
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 from flask import Flask\
from models.gamification_models import db\
from routes.gamification_routes import gamification_bp\
from services.xp_manager import xp_manager\
from services.challenge_manager import challenge_manager\
\
app = Flask(__name__)\
\
# Configurazione database\
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'  # Il tuo Neon DB\
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False\
\
# Inizializza database\
db.init_app(app)\
\
# Inizializza servizi\
xp_manager.init_app(app)\
challenge_manager.init_app(app)\
\
# Registra blueprint\
app.register_blueprint(gamification_bp)\
\
if __name__ == '__main__':\
    app.run(debug=True)\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 3. Configurazione Autenticazione\
\pard\pardeftab720\sa240\partightenfactor0

\fs24 \cf0 Modifica il decorator 
\f3\fs26 @login_required
\f0\fs24  in 
\f3\fs26 gamification_routes.py
\f0\fs24 :
\f1\b0 \
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 def login_required(f):\
    @wraps(f)\
    def decorated_function(*args, **kwargs):\
        # SOSTITUISCI CON LA TUA LOGICA DI AUTH\
        # Esempio con session:\
        user_id = session.get('user_id')\
        \
        # Oppure con JWT:\
        # token = request.headers.get('Authorization')\
        # user_id = verify_jwt(token)\
        \
        if not user_id:\
            return jsonify(\{'error': 'Non autenticato'\}), 401\
        \
        request.user_id = user_id\
        return f(*args, **kwargs)\
    return decorated_function\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 4. Setup Tracking Automatico\
\pard\pardeftab720\sa240\partightenfactor0

\fs24 \cf0 Integra il tracking XP nelle tue routes esistenti:
\f1\b0 \
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 # Nel tuo routes/messaggi.py (esempio)\
from services.xp_manager import xp_manager\
\
@app.route('/api/messages/send', methods=['POST'])\
@login_required\
def send_message():\
    # ... tua logica invio messaggio ...\
    \
    # AGGIUNGI TRACKING XP\
    xp_manager.xp_messaggio(\
        user_id=current_user_id,\
        is_primo_oggi=True,  # check se \'e8 primo messaggio oggi\
        risposta_veloce=False,\
        con_emoji=True,\
        gruppo=False\
    )\
    \
    # AGGIORNA PROGRESSO SFIDE\
    from services.challenge_manager import challenge_manager\
    challenge_manager.aggiorna_progresso(\
        user_id=current_user_id,\
        challenge_type='messaggio',\
        action_data=\{'count': 1\}\
    )\
    \
    return jsonify(\{'success': True\})\
\pard\pardeftab720\sa240\partightenfactor0

\f0\b\fs24 \cf0 Esempio per chatbot:
\f1\b0 \
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 @app.route('/api/chatbot/message', methods=['POST'])\
@login_required\
def chatbot_message():\
    # ... tua logica chatbot ...\
    \
    # TRACKING XP\
    xp_manager.xp_chatbot(\
        user_id=current_user_id,\
        is_prima_oggi=False,\
        conversazione_lunga=False,\
        per_studio=True\
    )\
    \
    # AGGIORNA SFIDE\
    challenge_manager.aggiorna_progresso(\
        user_id=current_user_id,\
        challenge_type='chatbot',\
        action_data=\{'count': 1\}\
    )\
    \
    return jsonify(\{'response': bot_response\})\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 5. Setup Scheduler (APScheduler)\
\pard\pardeftab720\sa240\partightenfactor0

\fs24 \cf0 Aggiungi in 
\f3\fs26 app.py
\f0\fs24 :
\f1\b0 \
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 from apscheduler.schedulers.background import BackgroundScheduler\
from services.xp_manager import xp_manager\
from services.challenge_manager import challenge_manager\
\
scheduler = BackgroundScheduler()\
\
# Reset XP giornaliero (ogni giorno a mezzanotte)\
scheduler.add_job(\
    func=xp_manager.reset_xp_giornaliero,\
    trigger="cron",\
    hour=0,\
    minute=0\
)\
\
# Assegna sfide giornaliere (ogni giorno alle 00:01)\
scheduler.add_job(\
    func=challenge_manager.assegna_sfide_giornaliere_globale,\
    trigger="cron",\
    hour=0,\
    minute=1\
)\
\
# Reset XP settimanale + assegna sfide (ogni luned\'ec a mezzanotte)\
scheduler.add_job(\
    func=xp_manager.reset_xp_settimanale,\
    trigger="cron",\
    day_of_week='mon',\
    hour=0,\
    minute=0\
)\
\
scheduler.add_job(\
    func=challenge_manager.assegna_sfide_settimanali_globale,\
    trigger="cron",\
    day_of_week='mon',\
    hour=0,\
    minute=1\
)\
\
scheduler.start()\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55356 \u57263  API ENDPOINTS DISPONIBILI\
\pard\pardeftab720\sa280\partightenfactor0

\fs28 \cf0 User Profile & Stats\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/profile          # Profilo completo utente\
GET  /api/gamification/stats            # Statistiche dettagliate\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Challenges\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/challenges/active       # Tutte le sfide attive\
GET  /api/gamification/challenges/daily        # Sfida giornaliera\
GET  /api/gamification/challenges/weekly       # Sfide settimanali\
GET  /api/gamification/challenges/class/:id    # Sfide di classe\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Badges\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/badges           # Badge posseduti + da sbloccare\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Leaderboards\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/leaderboard/:tipo       # Classifica (lifetime, settimanale, etc.)\
GET  /api/gamification/leaderboard/smart       # Leaderboard intelligente\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Notifications\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/notifications            # Notifiche utente\
POST /api/gamification/notifications/:id/read   # Segna come letta\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Battle Pass\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/battlepass       # Info battle pass stagione\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Social\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 POST /api/gamification/kudos            # Dai kudos a compagno\
GET  /api/gamification/kudos/received   # Kudos ricevuti\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Power-ups\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 GET  /api/gamification/powerups/available      # Power-ups acquistabili\
POST /api/gamification/powerups/buy            # Acquista power-up\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55356 \u57256  FRONTEND DASHBOARD (da implementare)\
\pard\pardeftab720\sa280\partightenfactor0

\fs28 \cf0 Dashboard Studente HTML/JS\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Crea 
\f2\fs26 templates/gamification_dashboard.html
\f1\fs24 :\
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 <!DOCTYPE html>\
<html lang="it">\
<head>\
    <meta charset="UTF-8">\
    <meta name="viewport" content="width=device-width, initial-scale=1.0">\
    <title>Dashboard Gamification - Skaila</title>\
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">\
    <style>\
        * \{\
            margin: 0;\
            padding: 0;\
            box-sizing: border-box;\
        \}\
        \
        body \{\
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\
            min-height: 100vh;\
            padding: 20px;\
        \}\
        \
        .dashboard \{\
            max-width: 1200px;\
            margin: 0 auto;\
        \}\
        \
        .card \{\
            background: white;\
            border-radius: 16px;\
            padding: 24px;\
            margin-bottom: 20px;\
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);\
        \}\
        \
        .profile-header \{\
            display: flex;\
            align-items: center;\
            gap: 20px;\
        \}\
        \
        .profile-avatar \{\
            width: 80px;\
            height: 80px;\
            border-radius: 50%;\
            background: linear-gradient(135deg, #667eea, #764ba2);\
            display: flex;\
            align-items: center;\
            justify-content: center;\
            font-size: 36px;\
        \}\
        \
        .profile-info h2 \{\
            font-size: 24px;\
            color: #1a202c;\
        \}\
        \
        .profile-rank \{\
            display: inline-block;\
            background: #fbbf24;\
            color: #92400e;\
            padding: 4px 12px;\
            border-radius: 12px;\
            font-size: 14px;\
            font-weight: 600;\
            margin-top: 8px;\
        \}\
        \
        .xp-bar \{\
            margin-top: 20px;\
        \}\
        \
        .xp-info \{\
            display: flex;\
            justify-content: space-between;\
            margin-bottom: 8px;\
            font-size: 14px;\
            color: #4b5563;\
        \}\
        \
        .progress-bar \{\
            height: 24px;\
            background: #e5e7eb;\
            border-radius: 12px;\
            overflow: hidden;\
        \}\
        \
        .progress-fill \{\
            height: 100%;\
            background: linear-gradient(90deg, #10b981, #34d399);\
            transition: width 0.3s ease;\
            display: flex;\
            align-items: center;\
            justify-content: center;\
            color: white;\
            font-weight: 600;\
            font-size: 12px;\
        \}\
        \
        .stats-grid \{\
            display: grid;\
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));\
            gap: 16px;\
            margin-top: 20px;\
        \}\
        \
        .stat-box \{\
            background: #f9fafb;\
            padding: 16px;\
            border-radius: 12px;\
            text-align: center;\
        \}\
        \
        .stat-value \{\
            font-size: 28px;\
            font-weight: 700;\
            color: #667eea;\
        \}\
        \
        .stat-label \{\
            font-size: 12px;\
            color: #6b7280;\
            margin-top: 4px;\
        \}\
        \
        .challenge-card \{\
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);\
            color: white;\
            padding: 20px;\
            border-radius: 12px;\
            margin-bottom: 12px;\
        \}\
        \
        .challenge-title \{\
            font-size: 18px;\
            font-weight: 600;\
            margin-bottom: 8px;\
        \}\
        \
        .challenge-progress \{\
            background: rgba(255,255,255,0.3);\
            height: 8px;\
            border-radius: 4px;\
            overflow: hidden;\
            margin: 12px 0;\
        \}\
        \
        .challenge-progress-fill \{\
            height: 100%;\
            background: white;\
            transition: width 0.3s ease;\
        \}\
        \
        .challenge-reward \{\
            display: flex;\
            align-items: center;\
            gap: 8px;\
            font-size: 14px;\
        \}\
        \
        .badge-grid \{\
            display: grid;\
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));\
            gap: 12px;\
        \}\
        \
        .badge-item \{\
            text-align: center;\
            padding: 12px;\
            background: #f9fafb;\
            border-radius: 12px;\
            cursor: pointer;\
            transition: transform 0.2s;\
        \}\
        \
        .badge-item:hover \{\
            transform: translateY(-4px);\
        \}\
        \
        .badge-icon \{\
            font-size: 36px;\
            margin-bottom: 8px;\
        \}\
        \
        .badge-name \{\
            font-size: 11px;\
            color: #6b7280;\
        \}\
        \
        .btn \{\
            padding: 12px 24px;\
            border: none;\
            border-radius: 8px;\
            font-weight: 600;\
            cursor: pointer;\
            transition: all 0.2s;\
        \}\
        \
        .btn-primary \{\
            background: #667eea;\
            color: white;\
        \}\
        \
        .btn-primary:hover \{\
            background: #5568d3;\
            transform: translateY(-2px);\
        \}\
    </style>\
</head>\
<body>\
    <div class="dashboard">\
        <!-- Profile Card -->\
        <div class="card">\
            <div class="profile-header">\
                <div class="profile-avatar" id="avatar">\
                    \uc0\u55356 \u57137 \
                </div>\
                <div class="profile-info">\
                    <h2 id="username">Caricamento...</h2>\
                    <span class="profile-rank" id="rank">\uc0\u55357 \u56624  Germoglio</span>\
                    <div>\uc0\u55357 \u56613  Streak: <strong id="streak">0</strong> giorni</div>\
                </div>\
            </div>\
            \
            <div class="xp-bar">\
                <div class="xp-info">\
                    <span id="xp-current">0 XP</span>\
                    <span id="xp-next">Prossimo: 200 XP</span>\
                </div>\
                <div class="progress-bar">\
                    <div class="progress-fill" id="xp-progress" style="width: 0%">0%</div>\
                </div>\
            </div>\
            \
            <div class="stats-grid">\
                <div class="stat-box">\
                    <div class="stat-value" id="stat-messages">0</div>\
                    <div class="stat-label">\uc0\u55357 \u56492  Messaggi</div>\
                </div>\
                <div class="stat-box">\
                    <div class="stat-value" id="stat-chatbot">0</div>\
                    <div class="stat-label">\uc0\u55358 \u56598  Chatbot</div>\
                </div>\
                <div class="stat-box">\
                    <div class="stat-value" id="stat-helps">0</div>\
                    <div class="stat-label">\uc0\u55358 \u56760  Aiuti</div>\
                </div>\
                <div class="stat-box">\
                    <div class="stat-value" id="stat-badges">0</div>\
                    <div class="stat-label">\uc0\u55356 \u57286  Badge</div>\
                </div>\
            </div>\
        </div>\
        \
        <!-- Daily Challenge -->\
        <div class="card">\
            <h3>\uc0\u55356 \u57263  Sfida del Giorno</h3>\
            <div id="daily-challenge">\
                <p>Caricamento...</p>\
            </div>\
        </div>\
        \
        <!-- Badges -->\
        <div class="card">\
            <h3>\uc0\u55356 \u57286  I Tuoi Badge</h3>\
            <div class="badge-grid" id="badges-grid">\
                <!-- Popolato da JS -->\
            </div>\
        </div>\
    </div>\
\
    <script>\
        // CONFIG\
        const API_BASE = '/api/gamification';\
        \
        // Load profile\
        async function loadProfile() \{\
            try \{\
                const response = await fetch(`$\{API_BASE\}/profile`, \{\
                    headers: \{\
                        'X-User-ID': getUserId()  // Sostituisci con tua logica auth\
                    \}\
                \});\
                \
                const data = await response.json();\
                \
                // Update UI\
                document.getElementById('username').textContent = data.user_id;  // Sostituisci con nome vero\
                document.getElementById('rank').textContent = data.rango.icon + ' ' + data.rango.attuale;\
                document.getElementById('streak').textContent = data.streak.attuale;\
                \
                // XP Bar\
                const xpPercent = data.xp.progresso_livello;\
                document.getElementById('xp-current').textContent = `$\{data.xp.totale\} XP`;\
                document.getElementById('xp-next').textContent = `Prossimo: $\{data.xp.per_prossimo_livello\} XP`;\
                document.getElementById('xp-progress').style.width = `$\{xpPercent\}%`;\
                document.getElementById('xp-progress').textContent = `$\{xpPercent\}%`;\
                \
                // Stats\
                document.getElementById('stat-messages').textContent = data.statistiche.messaggi_inviati;\
                document.getElementById('stat-chatbot').textContent = data.statistiche.chatbot_interazioni;\
                document.getElementById('stat-helps').textContent = data.statistiche.compagni_aiutati;\
                document.getElementById('stat-badges').textContent = data.statistiche.badge_totali;\
                \
                // Avatar icon based on rank\
                const rankIcons = \{\
                    'Germoglio': '\uc0\u55356 \u57137 ',\
                    'Cadetto': '\uc0\u55357 \u56624 ',\
                    'Cavaliere': '\uc0\u9876 \u65039 ',\
                    'Guardiano': '\uc0\u55357 \u57057 \u65039 ',\
                    'Campione': '\uc0\u55357 \u56401 ',\
                    'Leggenda': '\uc0\u11088 ',\
                    'Maestro': '\uc0\u55357 \u56462 ',\
                    'Grande Maestro': '\uc0\u55357 \u56613 ',\
                    'Immortale': '\uc0\u55356 \u57119 '\
                \};\
                document.getElementById('avatar').textContent = rankIcons[data.rango.attuale] || '\uc0\u55356 \u57262 ';\
                \
            \} catch (error) \{\
                console.error('Error loading profile:', error);\
            \}\
        \}\
        \
        // Load daily challenge\
        async function loadDailyChallenge() \{\
            try \{\
                const response = await fetch(`$\{API_BASE\}/challenges/daily`, \{\
                    headers: \{\
                        'X-User-ID': getUserId()\
                    \}\
                \});\
                \
                const challenge = await response.json();\
                \
                if (challenge) \{\
                    const progressPercent = challenge.percentuale || 0;\
                    \
                    const html = `\
                        <div class="challenge-card">\
                            <div class="challenge-title">$\{challenge.nome\}</div>\
                            <div style="font-size: 14px; opacity: 0.9;">$\{challenge.descrizione\}</div>\
                            <div class="challenge-progress">\
                                <div class="challenge-progress-fill" style="width: $\{progressPercent\}%"></div>\
                            </div>\
                            <div class="challenge-reward">\
                                <span>\uc0\u55356 \u57217  Ricompensa:</span>\
                                <span>$\{challenge.reward_xp\} XP</span>\
                                $\{challenge.reward_badge ? `+ \uc0\u55356 \u57286  Badge` : ''\}\
                            </div>\
                        </div>\
                    `;\
                    \
                    document.getElementById('daily-challenge').innerHTML = html;\
                \} else \{\
                    document.getElementById('daily-challenge').innerHTML = '<p>Nessuna sfida disponibile oggi</p>';\
                \}\
                \
            \} catch (error) \{\
                console.error('Error loading challenge:', error);\
            \}\
        \}\
        \
        // Load badges\
        async function loadBadges() \{\
            try \{\
                const response = await fetch(`$\{API_BASE\}/badges`, \{\
                    headers: \{\
                        'X-User-ID': getUserId()\
                    \}\
                \});\
                \
                const data = await response.json();\
                const badges = data.posseduti.slice(0, 12);  // Primi 12\
                \
                let html = '';\
                badges.forEach(badge => \{\
                    html += `\
                        <div class="badge-item">\
                            <div class="badge-icon">$\{badge.icon\}</div>\
                            <div class="badge-name">$\{badge.nome\}</div>\
                        </div>\
                    `;\
                \});\
                \
                document.getElementById('badges-grid').innerHTML = html || '<p>Nessun badge ancora</p>';\
                \
            \} catch (error) \{\
                console.error('Error loading badges:', error);\
            \}\
        \}\
        \
        // Helper: Get user ID (sostituisci con tua logica)\
        function getUserId() \{\
            // Esempio: leggi da cookie, session storage, o JWT\
            return '1';  // PLACEHOLDER\
        \}\
        \
        // Init\
        document.addEventListener('DOMContentLoaded', () => \{\
            loadProfile();\
            loadDailyChallenge();\
            loadBadges();\
            \
            // Refresh ogni 30 secondi\
            setInterval(() => \{\
                loadProfile();\
                loadDailyChallenge();\
            \}, 30000);\
        \});\
    </script>\
</body>\
</html>\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u9889  SOCKET.IO Real-time (opzionale)\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Per notifiche real-time, aggiungi in 
\f2\fs26 app.py
\f1\fs24 :\
\pard\pardeftab720\partightenfactor0

\f2\fs26 \cf0 from flask_socketio import SocketIO, emit\
\
socketio = SocketIO(app, cors_allowed_origins="*")\
\
@socketio.on('connect')\
def handle_connect():\
    print('Client connected')\
\
# Funzione helper per inviare notifiche\
def send_notification_realtime(user_id, notification_data):\
    socketio.emit('notification', notification_data, room=f'user_\{user_id\}')\
\
# Modifica in xp_manager.py per inviare notifiche real-time\
# quando assegni XP/badge/rank up\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55357 \u56522  METRICHE E MONITORING\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Crea dashboard analytics per monitorare:\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls1\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 DAU (Daily Active Users)\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 XP medi per utente\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Completion rate sfide\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Badge pi\'f9 rari\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Top leaderboard\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55357 \u56615  TROUBLESHOOTING\
\pard\pardeftab720\sa280\partightenfactor0

\fs28 \cf0 Database connection error\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 Verifica la stringa di connessione PostgreSQL in app.config\
Assicurati che Neon.tech abbia IP whitelist corretta\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 Sfide non assegnate automaticamente\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 Verifica che APScheduler sia running\
Check logs scheduler con: scheduler.print_jobs()\
\pard\pardeftab720\sa280\partightenfactor0

\f0\b\fs28 \cf0 XP non aggiornati\
\pard\pardeftab720\partightenfactor0

\f2\b0\fs26 \cf0 Verifica chiamate a xp_manager nelle tue routes\
Check limiti giornalieri in XP_CONFIG\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55357 \u56541  TODO / ESTENSIONI FUTURE\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls2\ilvl0
\f1\b0\fs24 \cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Frontend dashboard completo con Chart.js\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Sistema duelli 1v1 UI\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Chat gamification integrata\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Admin panel per gestire sfide/badge\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Export statistiche CSV\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Integrazione notifiche email\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 [ ] Mobile app React Native\
\pard\pardeftab720\sa298\partightenfactor0

\f0\b\fs36 \cf0 \uc0\u55358 \u56605  SUPPORTO\
\pard\pardeftab720\sa240\partightenfactor0

\f1\b0\fs24 \cf0 Per domande o problemi, contatta il team di sviluppo.\
\pard\pardeftab720\partightenfactor0
\cf3 \strokec3 \
\pard\pardeftab720\sa240\partightenfactor0

\f0\b \cf0 \strokec2 Versione:
\f1\b0  1.0\uc0\u8232 
\f0\b Data:
\f1\b0  Novembre 2025\uc0\u8232 
\f0\b Progetto:
\f1\b0  Skaila - Sistema Gamification Scuole Medie\
}