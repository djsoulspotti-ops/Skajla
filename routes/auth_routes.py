
"""
SKAILA - Routes Autenticazione
Gestisce login, logout, registrazione e sessioni
"""

from flask import Blueprint, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database_manager import db_manager
from gamification import gamification_system
import bcrypt
import hashlib

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    """Hash sicuro con salt per produzione"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verifica password con bcrypt"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        # Fallback per hash SHA-256 esistenti
        return hashlib.sha256(password.encode()).hexdigest() == hashed

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"🔍 Login attempt - Email: {email}")

        with db_manager.get_connection() as conn:
            user = conn.execute('SELECT * FROM utenti WHERE email = ?', (email,)).fetchone()

            if user and verify_password(password, user['password_hash']) and user['attivo'] == 1:
                print(f"✅ Login successful for user: {user['nome']}")
                
                # Imposta sessione
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['nome'] = user['nome']
                session['cognome'] = user['cognome']
                session['ruolo'] = user['ruolo']
                session['email'] = user['email']
                session['classe'] = user['classe']

                # Aggiorna status
                conn.execute('''
                    UPDATE utenti 
                    SET ultimo_accesso = CURRENT_TIMESTAMP, status_online = 1, primo_accesso = 0
                    WHERE id = ?
                ''', (user['id'],))

                # Gamification - Login giornaliero
                try:
                    gamification_system.get_or_create_user_profile(user['id'])
                    streak_info = gamification_system.update_streak(user['id'])
                    
                    if streak_info and streak_info.get('streak_updated'):
                        gamification_system.award_xp(user['id'], 'login_daily', description="Login giornaliero")
                except Exception as e:
                    print(f"⚠️ Gamification error: {e}")

                return redirect('/dashboard')
            else:
                print(f"❌ Login failed - Invalid credentials")

        return render_template('login.html', error='Email o password non corretti')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            nome = request.form['nome']
            cognome = request.form['cognome']
            classe = request.form.get('classe', '')
            ruolo = request.form.get('ruolo', 'studente')

            with db_manager.get_connection() as conn:
                # Controlla duplicati
                existing = conn.execute('SELECT id FROM utenti WHERE email = ? OR username = ?', (email, username)).fetchone()
                if existing:
                    return render_template('register.html', error='Email o username già esistenti')

                # Crea utente
                password_hash = hash_password(password)
                cursor = conn.execute('''
                    INSERT INTO utenti (username, email, password_hash, nome, cognome, classe, ruolo, primo_accesso)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ''', (username, email, password_hash, nome, cognome, classe, ruolo))

                user_id = cursor.lastrowid

                # Crea profilo AI
                conn.execute('''
                    INSERT INTO ai_profiles (utente_id, bot_name, conversation_style)
                    VALUES (?, ?, ?)
                ''', (user_id, f'SKAILA Assistant per {nome}', 'friendly'))

                # Auto-login
                session.permanent = True
                session['user_id'] = user_id
                session['username'] = username
                session['nome'] = nome
                session['cognome'] = cognome
                session['ruolo'] = ruolo
                session['email'] = email
                session['classe'] = classe
                session['primo_accesso'] = True

                flash('Registrazione completata con successo! 🎉', 'success')
                return redirect('/dashboard')

        except Exception as e:
            return render_template('register.html', error=f'Errore durante la registrazione: {str(e)}')

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        with db_manager.get_connection() as conn:
            conn.execute('UPDATE utenti SET status_online = 0 WHERE id = ?', (session['user_id'],))
    
    session.clear()
    return redirect('/')
