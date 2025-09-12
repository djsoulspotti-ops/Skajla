
"""
SKAILA - Routes Autenticazione
Gestisce login, logout, registrazione e sessioni
"""

from flask import Blueprint, render_template, request, redirect, session, flash

from services.auth_service import auth_service
from gamification import gamification_system  
from school_system import school_system
from database_manager import db_manager

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
            session['scuola_id'] = user.get('scuola_id')
            session['classe_id'] = user.get('classe_id')
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
            
            # Gestione scuola e classe - Trova ID scuola predefinita
            scuola_id_input = request.form.get('scuola_id')
            if scuola_id_input:
                scuola_id = int(scuola_id_input)
            else:
                # Lookup scuola predefinita invece di hardcode
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('SELECT id FROM scuole WHERE codice_pubblico = %s', ('DEFAULT_SCHOOL',))
                    else:
                        cursor.execute('SELECT id FROM scuole WHERE codice_pubblico = ?', ('DEFAULT_SCHOOL',))
                    default_school = cursor.fetchone()
                    if default_school:
                        scuola_id = default_school[0]
                    else:
                        flash('Errore: nessuna scuola predefinita configurata. Seleziona una scuola.', 'error')
                        return render_template('register.html', scuole=school_system.get_user_schools())
            classe_nome = request.form.get('classe_nome', '').strip()
            
            # Security: Ruolo assegnato in base al tipo registrazione
            ruolo = 'studente'  # Default studente
            codice_docente = request.form.get('codice_docente', '').strip()
            codice_dirigente = request.form.get('codice_dirigente', '').strip()
            
            # Verifica se è un dirigente (priorità massima)
            if codice_dirigente:
                # Verifica codice dirigente valido per la scuola
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('SELECT id FROM scuole WHERE id = %s AND codice_dirigente = %s', 
                                     (scuola_id, codice_dirigente))
                    else:
                        cursor.execute('SELECT id FROM scuole WHERE id = ? AND codice_dirigente = ?', 
                                     (scuola_id, codice_dirigente))
                    
                    if cursor.fetchone():
                        ruolo = 'dirigente'
                    else:
                        flash('Codice dirigente non valido per questa scuola', 'error')
                        return render_template('register.html', scuole=school_system.get_user_schools())
            
            # Verifica se è un docente (solo se non è già dirigente)
            elif codice_docente:
                # Verifica codice docente valido per la scuola
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('SELECT id FROM scuole WHERE id = %s AND codice_invito_docenti = %s', 
                                     (scuola_id, codice_docente))
                    else:
                        cursor.execute('SELECT id FROM scuole WHERE id = ? AND codice_invito_docenti = ?', 
                                     (scuola_id, codice_docente))
                    
                    if cursor.fetchone():
                        ruolo = 'professore'
                    else:
                        flash('Codice docente non valido per questa scuola', 'error')
                        return render_template('register.html', scuole=school_system.get_user_schools())
            
            # Gestione classe
            classe_id = None
            if classe_nome:
                # Cerca classe esistente o creane una nuova
                existing_classes = school_system.get_school_classes(scuola_id)
                existing_class = next((c for c in existing_classes if c[1].lower() == classe_nome.lower()), None)
                
                if existing_class:
                    classe_id = existing_class[0]
                else:
                    # Crea nuova classe
                    classe_id = school_system.create_class(scuola_id, classe_nome)
            
            # Crea utente con sistema scolastico
            result = auth_service.create_user(username, email, password, nome, cognome, ruolo, 
                                            classe_nome, scuola_id, classe_id)
            
            if result['success']:
                # Se è un professore, associalo alla classe
                if ruolo == 'professore' and classe_id and 'user_id' in result:
                    school_system.assign_teacher_to_class(result['user_id'], classe_id)
                
                flash('Registrazione completata! Effettua il login.', 'success')
                return redirect('/login')
            else:
                flash(result['message'], 'error')
                
        except Exception as e:
            flash(f'Errore durante la registrazione: {str(e)}', 'error')
    
    # GET: Mostra form con scuole disponibili
    scuole = school_system.get_user_schools()
    return render_template('register.html', scuole=scuole)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')
