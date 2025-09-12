
"""
SKAILA - Routes Autenticazione
Gestisce login, logout, registrazione e sessioni
"""

from flask import Blueprint, render_template, request, redirect, session, flash

from services.auth_service import auth_service
from gamification import gamification_system

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Verifica credenziali
        user = auth_service.authenticate_user(email, password)
        
        if user:
            # Crea sessione
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nome'] = user['nome']
            session['cognome'] = user['cognome']
            session['email'] = user['email']
            session['ruolo'] = user['ruolo']
            session['classe'] = user.get('classe', '')
            session['avatar'] = user.get('avatar', 'default.jpg')
            session.permanent = True
            
            # Aggiorna gamification
            gamification_system.update_streak(user['id'])
            gamification_system.award_xp(user['id'], 'login_daily', description="Login giornaliero")
            
            return redirect('/dashboard')
        else:
            flash('Email o password errati', 'error')
    
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
            # Security: Don't allow users to set their own role - always default to student
            ruolo = 'studente'  # Only admins can assign other roles
            classe = request.form.get('classe', '')
            
            # Crea utente
            result = auth_service.create_user(username, email, password, nome, cognome, ruolo, classe)
            
            if result['success']:
                flash('Registrazione completata! Effettua il login.', 'success')
                return redirect('/login')
            else:
                flash(result['message'], 'error')
                
        except Exception as e:
            flash(f'Errore durante la registrazione: {str(e)}', 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')
