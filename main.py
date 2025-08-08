
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import time
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'skaila_super_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE = 'skaila.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inizializza il database con tutte le tabelle necessarie"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop existing tables to ensure clean schema
    cursor.execute('DROP TABLE IF EXISTS messaggi')
    cursor.execute('DROP TABLE IF EXISTS partecipanti_canali')
    cursor.execute('DROP TABLE IF EXISTS canali')
    cursor.execute('DROP TABLE IF EXISTS users')
    
    # Tabella users (unificata)
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            ruolo TEXT DEFAULT 'studente',
            scuola TEXT,
            xp_totale INTEGER DEFAULT 0,
            livello INTEGER DEFAULT 1,
            data_registrazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_accesso DATETIME,
            attivo BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabella canali
    cursor.execute('''
        CREATE TABLE canali (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descrizione TEXT,
            tipo TEXT DEFAULT 'generale',
            creato_da INTEGER,
            data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
            attivo BOOLEAN DEFAULT 1,
            FOREIGN KEY (creato_da) REFERENCES users (id)
        )
    ''')
    
    # Tabella messaggi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messaggi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canale_id INTEGER,
            mittente_id INTEGER,
            contenuto TEXT NOT NULL,
            is_ai BOOLEAN DEFAULT 0,
            data_invio DATETIME DEFAULT CURRENT_TIMESTAMP,
            letto BOOLEAN DEFAULT 0,
            FOREIGN KEY (canale_id) REFERENCES canali (id),
            FOREIGN KEY (mittente_id) REFERENCES users (id)
        )
    ''')
    
    # Tabella partecipanti canali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partecipanti_canali (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            canale_id INTEGER,
            data_unione DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (canale_id) REFERENCES canali (id),
            UNIQUE(user_id, canale_id)
        )
    ''')
    
    # Inserisci dati di esempio
    
    # Utenti di esempio
    users = [
        ('demo@skaila.it', generate_password_hash('demo123'), 'Demo', 'User', 'studente', 'Liceo Demo', 50, 2),
        ('founder@skaila.it', generate_password_hash('founder123'), 'Founder', 'SKAILA', 'admin', 'SKAILA HQ', 1000, 10),
        ('prof.rossi@scuola.it', generate_password_hash('prof123'), 'Mario', 'Rossi', 'professore', 'Liceo Scientifico', 200, 5),
        ('lucia.bianchi@studenti.it', generate_password_hash('lucia123'), 'Lucia', 'Bianchi', 'studente', 'Liceo Scientifico', 120, 3)
    ]
    
    for user_data in users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (email, password_hash, nome, cognome, ruolo, scuola, xp_totale, livello) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', user_data)
    
    # Canali di esempio
    canali_esempio = [
        ('🏫 Generale', 'Comunicazioni generali della scuola', 'generale'),
        ('🤖 SKAILA AI Support', 'Assistente virtuale sempre disponibile', 'ai_support'),
        ('📚 Matematica', 'Discussioni e aiuto con la matematica', 'materia'),
        ('🔬 Scienze', 'Esperimenti e teoria scientifica', 'materia'),
        ('📖 Italiano', 'Letteratura e grammatica italiana', 'materia'),
        ('💼 SKAILA Connect', 'Opportunità di lavoro e stage', 'opportunita')
    ]
    
    for nome, desc, tipo in canali_esempio:
        cursor.execute('''
            INSERT OR IGNORE INTO canali (nome, descrizione, tipo, creato_da) 
            VALUES (?, ?, ?, ?)
        ''', (nome, desc, tipo, 1))
    
    # Messaggi di esempio
    messaggi_esempio = [
        (1, 1, "🎉 Benvenuti al nuovo anno scolastico! SKAILA è qui per rivoluzionare la comunicazione!", False),
        (2, None, "Ciao! 👋 Sono SKAILA AI, il vostro assistente virtuale. Sono qui per aiutarvi con qualsiasi domanda!", True),
        (3, 3, "📐 Oggi studieremo le equazioni di secondo grado. Chi ha domande?", False),
        (2, None, "💡 Le equazioni di secondo grado hanno la forma ax² + bx + c = 0. Il discriminante Δ = b² - 4ac!", True),
        (4, 4, "🧪 L'esperimento di oggi sarà sulla fotosintesi clorofilliana", False),
        (5, 3, "📚 Per domani leggete il capitolo sui Promessi Sposi", False),
        (6, 1, "💼 Nuove opportunità di stage disponibili per gli studenti del quinto anno!", False)
    ]
    
    for canale_id, mittente_id, contenuto, is_ai in messaggi_esempio:
        cursor.execute('''
            INSERT OR IGNORE INTO messaggi (canale_id, mittente_id, contenuto, is_ai) 
            VALUES (?, ?, ?, ?)
        ''', (canale_id, mittente_id, contenuto, is_ai))
    
    # Aggiungi tutti gli utenti ai canali pubblici
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    
    cursor.execute('SELECT id FROM canali WHERE tipo IN ("generale", "ai_support")')
    canali_pubblici = cursor.fetchall()
    
    for user in users:
        for canale in canali_pubblici:
            cursor.execute('''
                INSERT OR IGNORE INTO partecipanti_canali (user_id, canale_id) 
                VALUES (?, ?)
            ''', (user[0], canale[0]))
    
    conn.commit()
    conn.close()
    print("✅ Database inizializzato con successo!")

def genera_risposta_ai(messaggio):
    """Genera risposte intelligenti dell'AI"""
    risposte_saluto = [
        "Ciao! 👋 Sono SKAILA AI, il tuo assistente educativo. Come posso aiutarti oggi?",
        "Salve! Benvenuto su SKAILA. Sono qui per supportarti nell'apprendimento! 📚",
        "Hey! 🤖 Pronto ad aiutarti con qualsiasi domanda o dubbio!"
    ]
    
    risposte_aiuto = [
        "Posso aiutarti con: 📖 Spiegazioni di materie, 💡 Consigli di studio, 🧮 Risoluzione problemi, 📝 Correzione compiti",
        "Sono qui per supportarti! Chiedimi quello che vuoi su matematica, scienze, italiano o qualsiasi altra materia! 🎓",
        "🤝 Il mio obiettivo è aiutarti ad apprendere meglio. Fammi una domanda specifica!"
    ]
    
    risposte_matematica = [
        "Matematica! 🔢 La mia materia preferita! Su cosa hai bisogno di aiuto? Algebra, geometria, calcoli?",
        "📐 Perfetto! La matematica è logica pura. Dimmi qual è il problema e lo risolviamo insieme!",
        "🧮 Amo i numeri! Che tipo di esercizio o concetto matematico ti sta dando problemi?"
    ]
    
    risposte_scienze = [
        "Scienze! 🔬 Fantastico! Biologia, chimica, fisica... di cosa parliamo?",
        "🧪 La scienza è ovunque! Qual è l'argomento che ti interessa o su cui hai dubbi?",
        "⚗️ Esperimenti, teorie, formule... sono pronto per qualsiasi domanda scientifica!"
    ]
    
    risposte_generali = [
        "Interessante domanda! 🤔 Potresti essere più specifico così posso aiutarti meglio?",
        "💭 Ci sto pensando... puoi darmi più dettagli sulla tua richiesta?",
        "🎯 Per aiutarti al meglio, puoi riformulare la domanda in modo più specifico?",
        "📚 Ottima curiosità! Hai qualche argomento particolare in mente?",
        "🚀 Sono sempre pronto ad imparare cose nuove insieme a te! Dimmi di più!"
    ]
    
    messaggio_lower = messaggio.lower()
    
    if any(parola in messaggio_lower for parola in ['ciao', 'salve', 'hey', 'buongiorno', 'buonasera']):
        return random.choice(risposte_saluto)
    elif any(parola in messaggio_lower for parola in ['aiuto', 'help', 'supporto', 'come', 'cosa puoi']):
        return random.choice(risposte_aiuto)
    elif any(parola in messaggio_lower for parola in ['matematica', 'calcolo', 'equazione', 'algebra', 'geometria']):
        return random.choice(risposte_matematica)
    elif any(parola in messaggio_lower for parola in ['scienze', 'biologia', 'chimica', 'fisica', 'esperimento']):
        return random.choice(risposte_scienze)
    else:
        return random.choice(risposte_generali)

# ROUTES
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND attivo = 1',
            (email,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['nome'] = user['nome']
            session['cognome'] = user['cognome']
            session['ruolo'] = user['ruolo']
            session['email'] = user['email']
            return redirect(url_for('app_page'))
        else:
            return render_template('login.html', error='Email o password non corretti')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nome = request.form['nome']
        cognome = request.form['cognome']
        ruolo = request.form.get('ruolo', 'studente')
        scuola = request.form.get('scuola', '')
        
        if len(password) < 6:
            return render_template('register.html', error='La password deve essere di almeno 6 caratteri')
        
        conn = get_db_connection()
        
        # Controlla se l'email esiste già
        existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.close()
            return render_template('register.html', error='Email già registrata')
        
        # Crea nuovo utente
        password_hash = generate_password_hash(password)
        cursor = conn.execute('''
            INSERT INTO users (email, password_hash, nome, cognome, ruolo, scuola)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, nome, cognome, ruolo, scuola))
        
        user_id = cursor.lastrowid
        
        # Aggiungi ai canali pubblici
        conn.execute('''
            INSERT INTO partecipanti_canali (user_id, canale_id)
            SELECT ?, id FROM canali WHERE tipo IN ('generale', 'ai_support')
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        flash('Registrazione completata! Effettua il login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/app')
def app_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('app.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# API ROUTES
@app.route('/api/user')
def api_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    return jsonify({
        'id': session['user_id'],
        'nome': session['nome'],
        'cognome': session['cognome'],
        'ruolo': session['ruolo'],
        'email': session['email']
    })

@app.route('/api/canali')
def api_canali():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    conn = get_db_connection()
    canali = conn.execute('''
        SELECT c.id, c.nome, c.descrizione, c.tipo 
        FROM canali c
        JOIN partecipanti_canali pc ON c.id = pc.canale_id
        WHERE pc.user_id = ? AND c.attivo = 1
        ORDER BY c.tipo, c.nome
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return jsonify([dict(canale) for canale in canali])

@app.route('/api/messaggi/<int:canale_id>')
def api_messaggi(canale_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    conn = get_db_connection()
    messaggi = conn.execute('''
        SELECT m.*, u.nome, u.cognome, u.ruolo 
        FROM messaggi m
        LEFT JOIN users u ON m.mittente_id = u.id
        WHERE m.canale_id = ?
        ORDER BY m.data_invio ASC
        LIMIT 50
    ''', (canale_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(msg) for msg in messaggi])

# SOCKET.IO EVENTS
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        print(f"✅ {session['nome']} {session['cognome']} connesso")
    else:
        print("❌ Connessione non autenticata")

@socketio.on('join_channel')
def handle_join_channel(data):
    if 'user_id' not in session:
        return
    
    canale_id = data['canale_id']
    join_room(f"canale_{canale_id}")
    print(f"👥 {session['nome']} si è unito al canale {canale_id}")

@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return
    
    canale_id = data['canale_id']
    contenuto = data['contenuto']
    
    # Salva il messaggio
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO messaggi (canale_id, mittente_id, contenuto)
        VALUES (?, ?, ?)
    ''', (canale_id, session['user_id'], contenuto))
    
    messaggio_id = cursor.lastrowid
    
    # Ottieni info del canale
    canale_info = conn.execute(
        'SELECT nome, tipo FROM canali WHERE id = ?', (canale_id,)
    ).fetchone()
    
    conn.commit()
    conn.close()
    
    # Emetti il messaggio a tutti nel canale
    emit('new_message', {
        'id': messaggio_id,
        'canale_id': canale_id,
        'mittente_id': session['user_id'],
        'contenuto': contenuto,
        'nome': session['nome'],
        'cognome': session['cognome'],
        'ruolo': session['ruolo'],
        'data_invio': datetime.now().isoformat(),
        'is_ai': False
    }, room=f"canale_{canale_id}")
    
    # Attiva AI se necessario
    if canale_info and ('skaila' in contenuto.lower() or canale_info[1] == 'ai_support'):
        def risposta_ai():
            time.sleep(2)  # Delay realistico
            
            risposta = genera_risposta_ai(contenuto)
            
            conn = get_db_connection()
            cursor = conn.execute('''
                INSERT INTO messaggi (canale_id, mittente_id, contenuto, is_ai)
                VALUES (?, ?, ?, ?)
            ''', (canale_id, None, risposta, True))
            
            ai_msg_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            socketio.emit('new_message', {
                'id': ai_msg_id,
                'canale_id': canale_id,
                'mittente_id': None,
                'contenuto': risposta,
                'nome': 'SKAILA',
                'cognome': 'AI',
                'ruolo': 'ai',
                'data_invio': datetime.now().isoformat(),
                'is_ai': True
            }, room=f"canale_{canale_id}")
        
        threading.Thread(target=risposta_ai).start()

if __name__ == '__main__':
    init_db()
    print("🚀 SKAILA Server avviato!")
    print("📍 http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
