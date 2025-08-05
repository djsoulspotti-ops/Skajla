from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skaila-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE = 'skaila.db'

def init_db():
    """Inizializza il database SKAILA"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Tabella utenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                cognome TEXT NOT NULL,
                ruolo TEXT NOT NULL CHECK(ruolo IN ('studente', 'professore', 'genitore', 'dirigente', 'admin')),
                scuola TEXT,
                classe TEXT,
                xp_totale INTEGER DEFAULT 0,
                livello INTEGER DEFAULT 1,
                badge_ottenuti TEXT DEFAULT '[]',
                status TEXT DEFAULT 'offline',
                ultimo_accesso TIMESTAMP,
                data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabella canali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS canali (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descrizione TEXT,
                tipo TEXT NOT NULL CHECK(tipo IN ('generale', 'classe', 'materia', 'ai_support')),
                scuola TEXT NOT NULL,
                classe TEXT,
                materia TEXT,
                ai_abilitato BOOLEAN DEFAULT 1,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabella messaggi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messaggi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canale_id INTEGER NOT NULL,
                utente_id INTEGER,
                contenuto TEXT NOT NULL,
                ai_generato BOOLEAN DEFAULT 0,
                data_invio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (canale_id) REFERENCES canali (id),
                FOREIGN KEY (utente_id) REFERENCES users (id)
            )
        ''')

        # Tabella partecipanti canali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partecipanti_canali (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canale_id INTEGER NOT NULL,
                utente_id INTEGER NOT NULL,
                data_aggiunta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (canale_id) REFERENCES canali (id),
                FOREIGN KEY (utente_id) REFERENCES users (id),
                UNIQUE(canale_id, utente_id)
            )
        ''')

        # Tabella attività XP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attivita_xp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utente_id INTEGER NOT NULL,
                tipo_attivita TEXT NOT NULL,
                xp_guadagnati INTEGER NOT NULL,
                descrizione TEXT,
                data_attivita TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utente_id) REFERENCES users (id)
            )
        ''')

        # Inserisci dati di esempio
        cursor.execute('''
            INSERT OR IGNORE INTO users (email, password_hash, nome, cognome, ruolo, scuola, xp_totale, livello) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('demo@skaila.it', generate_password_hash('demo123'), 'Demo', 'User', 'studente', 'Liceo Demo', 50, 2))

        # Canali di esempio
        canali_esempio = [
            ('🏫 Generale', 'Comunicazioni generali della scuola', 'generale', 'Liceo Demo'),
            ('🤖 SKAILA AI', 'Assistente AI sempre disponibile', 'ai_support', 'Sistema'),
            ('📚 Matematica 3A', 'Discussioni di matematica per la 3A', 'materia', 'Liceo Demo'),
            ('📖 Italiano 2B', 'Letteratura e grammatica', 'materia', 'Liceo Demo'),
        ]

        for canale in canali_esempio:
            cursor.execute('''
                INSERT OR IGNORE INTO canali (nome, descrizione, tipo, scuola) 
                VALUES (?, ?, ?, ?)
            ''', canale)

        conn.commit()

def assegna_xp(utente_id, xp_amount, descrizione=""):
    """Assegna XP a un utente"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Registra l'attività
        cursor.execute('''
            INSERT INTO attivita_xp (utente_id, tipo_attivita, xp_guadagnati, descrizione)
            VALUES (?, ?, ?, ?)
        ''', (utente_id, 'azione', xp_amount, descrizione))

        # Aggiorna XP utente
        cursor.execute('SELECT xp_totale FROM users WHERE id = ?', (utente_id,))
        result = cursor.fetchone()
        if result:
            nuovo_xp = result[0] + xp_amount
            nuovo_livello = min(50, int((nuovo_xp / 100) ** 0.5) + 1)
            cursor.execute('UPDATE users SET xp_totale = ?, livello = ? WHERE id = ?', 
                         (nuovo_xp, nuovo_livello, utente_id))
            conn.commit()
            return nuovo_xp, nuovo_livello
        return 0, 1

def genera_risposta_ai(messaggio):
    """SKAILA AI Assistant - Genera risposte intelligenti"""
    risposte_saluto = [
        "Ciao! 👋 Sono SKAILA AI, il tuo assistente educativo. Come posso aiutarti oggi?",
        "Salve! Benvenuto su SKAILA. Sono qui per supportarti nell'apprendimento! 📚",
        "Hey! 🌟 Sono l'intelligenza artificiale di SKAILA. Dimmi, cosa posso fare per te?"
    ]

    risposte_aiuto = [
        "Posso aiutarti con: 📖 Spiegazioni di materie, 💡 Consigli di studio, 🤔 Risoluzione problemi, ❓ Domande sulla piattaforma!",
        "Sono specializzato nel supporto educativo! Chiedi pure di matematica, italiano, scienze, o qualsiasi altra materia! 🎯",
        "Perfetto! Sono qui per: ✅ Aiutarti con i compiti ✅ Spiegare concetti difficili ✅ Darti consigli di studio ✅ Rispondere alle tue domande!"
    ]

    risposte_matematica = [
        "Matematica! 🔢 La mia materia preferita! Su cosa hai bisogno di aiuto? Algebra, geometria, analisi, statistica?",
        "Ottimo! 📐 In matematica, ricorda: ogni problema si risolve passo dopo passo. Qual è il tuo dubbio specifico?",
        "Adoro la matematica! 🧮 Dimmi l'argomento o l'esercizio e ti aiuto a risolverlo insieme!"
    ]

    risposte_default = [
        "Interessante! 🤔 Potresti darmi più dettagli così posso aiutarti meglio?",
        "Bella domanda! 💭 Dimmi di più e sarò più preciso nella risposta.",
        "Sono qui per aiutarti! 🚀 Riformula la domanda o dammi più contesto per essere più utile."
    ]

    messaggio_lower = messaggio.lower()

    if any(parola in messaggio_lower for parola in ['ciao', 'salve', 'hey', 'buongiorno', 'buonasera']):
        return random.choice(risposte_saluto)
    elif any(parola in messaggio_lower for parola in ['aiuto', 'help', 'supporto', 'aiutami']):
        return random.choice(risposte_aiuto)
    elif any(parola in messaggio_lower for parola in ['matematica', 'calcolo', 'equazione', 'algebra', 'geometria']):
        return random.choice(risposte_matematica)
    else:
        return random.choice(risposte_default)

# Inizializza database
init_db()

# Routes principali
@app.route('/')
def home():
    """Landing page SKAILA"""
    return render_template('index.html')

@app.route('/app')
def main_app():
    """App principale di messaggistica"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('app.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Sistema di login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, email, nome, cognome, ruolo, password_hash FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[5], password):
                session['user_id'] = user[0]
                session['user_email'] = user[1]
                session['user_nome'] = user[2]
                session['user_cognome'] = user[3]
                session['user_ruolo'] = user[4]

                # Aggiorna ultimo accesso
                cursor.execute('UPDATE users SET status = ?, ultimo_accesso = ? WHERE id = ?', 
                             ('online', datetime.now(), user[0]))
                conn.commit()

                # XP per login
                assegna_xp(user[0], 5, "Login giornaliero")

                if request.is_json:
                    return jsonify({'success': True, 'redirect': '/app'})
                return redirect(url_for('main_app'))
            else:
                error = 'Email o password non corretti'
                if request.is_json:
                    return jsonify({'error': error}), 401
                return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Sistema di registrazione"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        email = data.get('email')
        password = data.get('password')
        nome = data.get('nome')
        cognome = data.get('cognome')
        ruolo = data.get('ruolo', 'studente')
        scuola = data.get('scuola')
        classe = data.get('classe', '')

        if not all([email, password, nome, cognome, scuola]):
            error = 'Tutti i campi sono obbligatori'
            if request.is_json:
                return jsonify({'error': error}), 400
            return render_template('register.html', error=error)

        password_hash = generate_password_hash(password)

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (email, password_hash, nome, cognome, ruolo, scuola, classe, xp_totale, livello)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (email, password_hash, nome, cognome, ruolo, scuola, classe, 20, 1))

                user_id = cursor.lastrowid

                # Aggiungi ai canali automaticamente
                cursor.execute('SELECT id FROM canali WHERE scuola = ? OR tipo = ?', (scuola, 'ai_support'))
                canali = cursor.fetchall()

                for canale in canali:
                    cursor.execute('INSERT OR IGNORE INTO partecipanti_canali (canale_id, utente_id) VALUES (?, ?)', 
                                 (canale[0], user_id))

                # XP di benvenuto
                assegna_xp(user_id, 20, "Benvenuto su SKAILA!")

                conn.commit()

                if request.is_json:
                    return jsonify({'success': True, 'message': 'Registrazione completata!'})
                return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            error = 'Email già registrata'
            if request.is_json:
                return jsonify({'error': error}), 400
            return render_template('register.html', error=error)

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout utente"""
    if 'user_id' in session:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET status = ? WHERE id = ?', ('offline', session['user_id']))
            conn.commit()

    session.clear()
    return redirect(url_for('home'))

# API Routes
@app.route('/api/canali')
def api_canali():
    """API - Lista canali utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.nome, c.descrizione, c.tipo, c.ai_abilitato,
                   COUNT(m.id) as num_messaggi
            FROM canali c
            JOIN partecipanti_canali pc ON c.id = pc.canale_id
            LEFT JOIN messaggi m ON c.id = m.canale_id
            WHERE pc.utente_id = ?
            GROUP BY c.id
            ORDER BY c.tipo, c.nome
        ''', (session['user_id'],))

        canali = []
        for row in cursor.fetchall():
            canali.append({
                'id': row[0],
                'nome': row[1],
                'descrizione': row[2],
                'tipo': row[3],
                'ai_abilitato': row[4],
                'num_messaggi': row[5]
            })

    return jsonify(canali)

@app.route('/api/messaggi/<int:canale_id>')
def api_messaggi(canale_id):
    """API - Messaggi di un canale"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.contenuto, m.data_invio, m.ai_generato,
                   u.nome, u.cognome, u.ruolo
            FROM messaggi m
            LEFT JOIN users u ON m.utente_id = u.id
            WHERE m.canale_id = ?
            ORDER BY m.data_invio ASC
            LIMIT 100
        ''', (canale_id,))

        messaggi = []
        for row in cursor.fetchall():
            messaggi.append({
                'id': row[0],
                'contenuto': row[1],
                'data_invio': row[2],
                'ai_generato': row[3],
                'autore': {
                    'nome': row[4] or 'SKAILA AI',
                    'cognome': row[5] or '',
                    'ruolo': row[6] or 'ai'
                }
            })

    return jsonify(messaggi)

@app.route('/api/user/stats')
def api_user_stats():
    """API - Statistiche utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.xp_totale, u.livello, u.nome, u.cognome, u.ruolo,
                   COUNT(DISTINCT m.id) as messaggi_inviati
            FROM users u
            LEFT JOIN messaggi m ON u.id = m.utente_id
            WHERE u.id = ?
            GROUP BY u.id
        ''', (session['user_id'],))

        result = cursor.fetchone()
        if result:
            return jsonify({
                'xp_totale': result[0],
                'livello': result[1],
                'nome': result[2],
                'cognome': result[3],
                'ruolo': result[4],
                'messaggi_inviati': result[5],
                'prossimo_livello_xp': ((result[1]) ** 2) * 100
            })

    return jsonify({'error': 'Utente non trovato'}), 404

# WebSocket per messaggistica real-time
@socketio.on('connect')
def on_connect():
    """Connessione WebSocket"""
    if 'user_id' in session:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT canale_id FROM partecipanti_canali WHERE utente_id = ?', (session['user_id'],))
            for row in cursor.fetchall():
                join_room(f"canale_{row[0]}")

        emit('connected', {'message': f'Benvenuto su SKAILA, {session.get("user_nome", "Utente")}!'})

@socketio.on('send_message')
def handle_message(data):
    """Gestione invio messaggi"""
    if 'user_id' not in session:
        return

    canale_id = data.get('canale_id')
    contenuto = data.get('contenuto')

    if not canale_id or not contenuto:
        return

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messaggi (canale_id, utente_id, contenuto) VALUES (?, ?, ?)', 
                      (canale_id, session['user_id'], contenuto))
        messaggio_id = cursor.lastrowid

        cursor.execute('SELECT nome, cognome, ruolo FROM users WHERE id = ?', (session['user_id'],))
        user_info = cursor.fetchone()

        cursor.execute('SELECT ai_abilitato, tipo FROM canali WHERE id = ?', (canale_id,))
        canale_info = cursor.fetchone()

        conn.commit()

    # XP per messaggio
    assegna_xp(session['user_id'], 2, "Messaggio inviato")

    # Invia messaggio a tutti
    messaggio_data = {
        'id': messaggio_id,
        'contenuto': contenuto,
        'canale_id': canale_id,
        'data_invio': datetime.now().isoformat(),
        'ai_generato': False,
        'autore': {
            'nome': user_info[0],
            'cognome': user_info[1],
            'ruolo': user_info[2]
        }
    }

    emit('new_message', messaggio_data, room=f"canale_{canale_id}")

    # Risposta AI automatica
    if canale_info and canale_info[0] and ('skaila' in contenuto.lower() or canale_info[1] == 'ai_support'):
        import threading
        import time

        def risposta_ai():
            time.sleep(2)
            risposta = genera_risposta_ai(contenuto)

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO messaggi (canale_id, contenuto, ai_generato) VALUES (?, ?, ?)',
                              (canale_id, risposta, True))
                ai_msg_id = cursor.lastrowid
                conn.commit()

            ai_msg_data = {
                'id': ai_msg_id,
                'contenuto': risposta,
                'canale_id': canale_id,
                'data_invio': datetime.now().isoformat(),
                'ai_generato': True,
                'autore': {'nome': 'SKAILA AI', 'cognome': '', 'ruolo': 'ai'}
            }

            socketio.emit('new_message', ai_msg_data, room=f"canale_{canale_id}")

        threading.Thread(target=risposta_ai).start()

@socketio.on('join_channel')
def on_join_channel(data):
    """Unisciti a un canale"""
    canale_id = data.get('canale_id')
    if canale_id:
        join_room(f"canale_{canale_id}")

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)

    print("🚀 SKAILA Backend starting...")
    print("📊 Database initialized")
    print("🤖 AI Assistant ready")
    print("🏆 XP System active")
    print("💬 Real-time messaging enabled")
    print("🎯 Ready to revolutionize Italian schools!")

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app.secret_key = "chiave_segreta_super_sicura"  # Cambiala con una chiave segreta vera

# Route Login - mostra il form
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Connessione al DB
        conn = sqlite3.connect("skaila.db")
        cursor = conn.cursor()

        # Cerca utente
        cursor.execute("SELECT * FROM utenti WHERE email = ? AND password = ?", (email, password))
        utente = cursor.fetchone()
        conn.close()

        if utente:
            session["utente"] = utente[1]  # Salviamo il nome utente in sessione
            return redirect(url_for("chat"))  # Vai alla chat
        else:
            flash("Email o password errati", "errore")
            return redirect(url_for("login"))

    return render_template("login.html")

# Route Chat - solo se loggati
@app.route("/chat")
def chat():
    if "utente" in session:
        return render_template("chat.html", utente=session["utente"])
    else:
        flash("Devi effettuare il login", "errore")
        return redirect(url_for("login"))