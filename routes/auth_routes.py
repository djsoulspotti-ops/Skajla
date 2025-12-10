
"""
SKAJLA - Routes Autenticazione
Gestisce login, logout, registrazione e sessioni
"""

import secrets
import bcrypt
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from csrf_protection import csrf_protect

from services.auth_service import auth_service
from services.password_validator import validate_password
from services.email_validator import validate_email, normalize_email
from gamification import gamification_system  
from school_system import school_system
from database_manager import db_manager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf_protect
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        print(f"🔐 Login attempt: {email} (Remember: {remember_me})")
        
        # Verifica lockout
        if auth_service.is_locked_out(email):
            import time
            last_attempt = auth_service.login_attempts.get(email, {}).get('last_attempt', 0)
            time_since_last_attempt = time.time() - last_attempt
            time_remaining = max(0, auth_service.lockout_duration - time_since_last_attempt)
            minutes_left = max(1, int(time_remaining / 60))  # Minimo 1 minuto per evitare confusione
            flash(f'⚠️ Troppi tentativi falliti. Riprova tra {minutes_left} minuti.', 'error')
            print(f"🔒 Login locked out: {email} - {minutes_left} minuti rimanenti")
            return render_template('login.html')
        
        # Verifica credenziali
        user = auth_service.authenticate_user(email, password)
        
        if user:
            print(f"✅ Login successful: {email}")
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
            
            # Gestione Remember Me: salva preferenza in sessione (NO modifica globale!)
            session.permanent = True  # Usa il lifetime configurato in main.py (30 giorni)
            session['remember_me'] = remember_me
            if remember_me:
                print(f"✅ Remember Me attivo: sessione 30 giorni")
            else:
                # Sessione breve: salva timestamp per controllo scadenza
                from datetime import datetime, timedelta
                session['session_expires'] = (datetime.utcnow() + timedelta(days=1)).isoformat()
                print(f"✅ Sessione breve: 1 giorno")
            
            # Aggiorna gamification
            try:
                gamification_system.update_streak(user['id'])
                gamification_system.award_xp(user['id'], 'login_daily', multiplier=1.0, context="Login giornaliero")
            except Exception as e:
                print(f"⚠️ Gamification error (non-blocking): {e}")
            
            flash(f'👋 Bentornato, {user["nome"]}!', 'success')
            return redirect('/dashboard')
        else:
            print(f"❌ Login failed: {email}")
            flash('❌ Email o password errati. Controlla le credenziali e riprova.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf_protect
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            nome = request.form['nome']
            cognome = request.form['cognome']
            
            # Validazione email
            is_valid_email, email_message = validate_email(email)
            if not is_valid_email:
                flash(f'❌ Email non valida: {email_message}', 'error')
                return render_template('register.html', scuole=school_system.get_user_schools())
            
            # Normalizza email
            email = normalize_email(email)
            
            # Validazione password robusta
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(f'❌ Password non valida: {message}', 'error')
                return render_template('register.html', scuole=school_system.get_user_schools())
            
            # NUOVO SISTEMA: Codici Scuola Premium (PRIORITÀ ASSOLUTA)
            codice_scuola_premium = request.form.get('codice_scuola_premium', '').strip().upper()
            scuola_id = None
            
            # Leggi ruolo dal form (default: studente)
            ruolo_from_form = request.form.get('ruolo', 'studente').strip()
            # Valida ruolo
            valid_roles = ['studente', 'professore', 'genitore', 'dirigente']
            ruolo = ruolo_from_form if ruolo_from_form in valid_roles else 'studente'
            
            # PRIORITÀ 1: Codice Scuola Premium (SKAIL, PROF, DIR)
            if codice_scuola_premium:
                from services.school_codes_manager import school_codes_manager
                
                # Verifica codice in school_activation_codes
                codice_info = db_manager.query("""
                    SELECT id, school_name, school_code, teacher_invite_code, 
                           director_code, assigned, assigned_to_school_id
                    FROM school_activation_codes
                    WHERE school_code = %s OR teacher_invite_code = %s OR director_code = %s
                """, (codice_scuola_premium, codice_scuola_premium, codice_scuola_premium), one=True)
                
                if not codice_info:
                    flash('❌ Codice scuola non valido. Verifica e riprova.', 'error')
                    return render_template('register.html', scuole=school_system.get_user_schools())
                
                # Determina ruolo dal tipo di codice
                if codice_scuola_premium == codice_info['director_code']:
                    ruolo = 'dirigente'
                elif codice_scuola_premium == codice_info['teacher_invite_code']:
                    ruolo = 'professore'
                else:  # school_code
                    ruolo = 'studente'
                
                # Se già assegnato, usa scuola esistente
                if codice_info['assigned'] and codice_info['assigned_to_school_id']:
                    scuola_id = codice_info['assigned_to_school_id']
                    print(f"✅ Codice già assegnato - Scuola ID: {scuola_id}")
                else:
                    # RACE CONDITION PROTECTION: Transazione atomica per creazione scuola
                    print(f"🏫 Creazione nuova scuola: {codice_info['school_name']}")
                    try:
                        with db_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            
                            # Lock esclusivo su riga codice per prevenire race condition
                            cursor.execute("""
                                SELECT assigned, assigned_to_school_id 
                                FROM school_activation_codes 
                                WHERE id = %s 
                                FOR UPDATE
                            """, (codice_info['id'],))
                            
                            locked_row = cursor.fetchone()
                            
                            # Double-check se già assegnato durante il lock
                            if locked_row and locked_row[0]:
                                scuola_id = locked_row[1]
                                print(f"✅ Scuola già creata da altra richiesta - ID: {scuola_id}")
                            else:
                                # Crea scuola
                                cursor.execute("""
                                    INSERT INTO scuole (nome, codice_pubblico, codice_invito_docenti, 
                                                      codice_dirigente, attiva, created_at)
                                    VALUES (%s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                                    RETURNING id
                                """, (codice_info['school_name'], codice_info['school_code'],
                                      codice_info['teacher_invite_code'], codice_info['director_code']))
                                
                                scuola_id = cursor.fetchone()[0]
                                
                                # Marca codice come assegnato
                                cursor.execute("""
                                    UPDATE school_activation_codes
                                    SET assigned = TRUE, assigned_to_school_id = %s, assigned_at = CURRENT_TIMESTAMP
                                    WHERE id = %s
                                """, (scuola_id, codice_info['id']))
                                
                                conn.commit()
                                print(f"✅ Scuola creata con ID: {scuola_id}")
                                
                    except Exception as e:
                        print(f"❌ Errore creazione scuola: {e}")
                        flash('Errore durante la creazione della scuola. Riprova.', 'error')
                        return render_template('register.html', scuole=school_system.get_user_schools())
                
                flash(f'✅ Codice valido! Registrazione come {ruolo} per {codice_info["school_name"]}', 'success')
            
            # PRIORITÀ 2: Selezione scuola manuale (vecchio sistema)
            else:
                scuola_id_input = request.form.get('scuola_id')
                if scuola_id_input:
                    scuola_id = int(scuola_id_input)
                else:
                    # Usa sempre scuola predefinita se non specificato
                    default_school = db_manager.query(
                        'SELECT id FROM scuole WHERE codice_pubblico = %s', 
                        ('DEFAULT_SCHOOL',), one=True
                    )
                    if default_school:
                        scuola_id = default_school['id']
                        print(f"✅ Registrazione semplice: assegnato a scuola predefinita (ID: {scuola_id})")
                    else:
                        # Crea scuola predefinita al volo se non esiste
                        try:
                            with db_manager.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO scuole (nome, codice_pubblico, codice_invito_docenti, 
                                                      codice_dirigente, attiva, created_at)
                                    VALUES (%s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                                    RETURNING id
                                """, ('SKAJLA Community', 'DEFAULT_SCHOOL', 'DEFAULT_TEACHER', 'DEFAULT_DIRECTOR'))
                                scuola_id = cursor.fetchone()[0]
                                conn.commit()
                                print(f"✅ Scuola predefinita creata (ID: {scuola_id})")
                        except Exception as e:
                            print(f"❌ Errore creazione scuola predefinita: {e}")
                            flash('Errore durante la registrazione. Riprova.', 'error')
                            return render_template('register.html', scuole=school_system.get_user_schools())
            
            classe_nome = request.form.get('classe_nome', '').strip()
            codice_docente = request.form.get('codice_docente', '').strip()
            codice_dirigente = request.form.get('codice_dirigente', '').strip()
            personal_code = request.form.get('personal_code', '').strip()
            personal_code_id = None
            
            # PRIORITÀ 1: Verifica codice personale (nuovo sistema automatico)
            if personal_code:
                validation = school_system.verify_personal_code(personal_code)
                if not validation['success']:
                    flash(validation['message'], 'error')
                    return render_template('register.html', scuole=school_system.get_user_schools())
                
                # Email deve corrispondere al codice personale
                if email != validation['email']:
                    flash('Email non corrisponde al codice personale', 'error')
                    return render_template('register.html', scuole=school_system.get_user_schools())
                
                # Imposta ruolo e scuola dal codice personale
                ruolo = validation['role']
                scuola_id = validation['school_id']
                personal_code_id = validation['code_id']
                
                flash(f'Codice personale validato! Registrazione come {ruolo} per {validation["school_name"]}', 'success')
            
            # PRIORITÀ 2: Verifica se è un dirigente (solo se non ha codice personale)
            elif codice_dirigente and not personal_code:
                # Verifica codice dirigente valido per la scuola
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('SELECT id FROM scuole WHERE id = %s AND codice_dirigente = %s', 
                                     (scuola_id, codice_dirigente))
                    else:
                        cursor.execute('SELECT id FROM scuole WHERE id = %s AND codice_dirigente = %s', 
                                     (scuola_id, codice_dirigente))
                    
                    if cursor.fetchone():
                        ruolo = 'dirigente'
                    else:
                        flash('Codice dirigente non valido per questa scuola', 'error')
                        return render_template('register.html', scuole=school_system.get_user_schools())
            
            # PRIORITÀ 3: Verifica se è un docente (solo se non è già dirigente o personal code)
            elif codice_docente and not personal_code:
                # Verifica codice docente valido per la scuola
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('SELECT id FROM scuole WHERE id = %s AND codice_invito_docenti = %s', 
                                     (scuola_id, codice_docente))
                    else:
                        cursor.execute('SELECT id FROM scuole WHERE id = %s AND codice_invito_docenti = %s', 
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
                user_id = result['user_id']
                
                # IMPORTANTE: Marca codice personale come usato se utilizzato
                if personal_code_id is not None:
                    school_system.mark_personal_code_used(personal_code_id, user_id)
                    flash(f'Registrazione completata! Codice personale {personal_code} consumato.', 'success')
                else:
                    flash('Registrazione completata! Effettua il login.', 'success')
                
                # Se è un professore, associalo alla classe
                if ruolo == 'professore' and classe_id:
                    school_system.assign_teacher_to_class(user_id, classe_id)
                
                # AUTO-CREAZIONE CHAT ROOM DI CLASSE (Task 14)
                if classe_nome and scuola_id:
                    try:
                        # Cerca o crea chat room di classe
                        chat_nome = f"Classe {classe_nome} - Chat Generale"
                        chat_room = db_manager.query('''
                            SELECT id FROM chat 
                            WHERE scuola_id = %s AND classe = %s AND tipo = %s
                        ''', (scuola_id, classe_nome, 'classe'), one=True)
                        
                        if not chat_room:
                            # Crea nuova chat room di classe
                            chat_id = db_manager.query('''
                                INSERT INTO chat (nome, tipo, classe, scuola_id, created_at, attiva)
                                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, TRUE)
                                RETURNING id
                            ''', (chat_nome, 'classe', classe_nome, scuola_id), one=True)['id']
                            print(f"✅ Chat room classe {classe_nome} creata (ID: {chat_id})")
                        else:
                            chat_id = chat_room['id']
                            print(f"✅ Chat room classe {classe_nome} trovata (ID: {chat_id})")
                        
                        # Aggiungi utente alla chat room
                        existing_participant = db_manager.query('''
                            SELECT id FROM partecipanti_chat 
                            WHERE chat_id = %s AND utente_id = %s
                        ''', (chat_id, user_id), one=True)
                        
                        if not existing_participant:
                            db_manager.execute('''
                                INSERT INTO partecipanti_chat (chat_id, utente_id, joined_at)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ''', (chat_id, user_id))
                            print(f"✅ Utente {user_id} aggiunto a chat {chat_id}")
                            flash(f'🎉 Sei stato automaticamente aggiunto alla chat della tua classe!', 'success')
                        
                        # AUTO-AGGIUNTA AI GRUPPI MATERIA PREDEFINITI
                        try:
                            from services.messaging.subject_groups_initializer import add_student_to_subject_groups
                            add_student_to_subject_groups(user_id, scuola_id, classe_nome)
                            print(f"✅ Studente {user_id} aggiunto ai gruppi materia della classe {classe_nome}")
                        except Exception as e:
                            print(f"⚠️ Errore aggiungendo studente ai gruppi materia: {e}")
                    except Exception as e:
                        print(f"⚠️ Errore auto-creazione chat (non-blocking): {e}")
                
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

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@csrf_protect
def forgot_password():
    reset_link = None
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Per favore inserisci un indirizzo email.', 'error')
            return render_template('forgot_password.html')
        
        user = db_manager.query(
            'SELECT id, email, nome FROM utenti WHERE LOWER(email) = %s',
            (email,), one=True
        )
        
        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            db_manager.execute(
                'UPDATE password_reset_tokens SET used = TRUE WHERE user_id = %s AND used = FALSE',
                (user['id'],)
            )
            
            db_manager.execute('''
                INSERT INTO password_reset_tokens (user_id, token, expires_at, used, created_at)
                VALUES (%s, %s, %s, FALSE, CURRENT_TIMESTAMP)
            ''', (user['id'], token, expires_at))
            
            reset_link = request.host_url.rstrip('/') + f'/reset-password/{token}'
            
            print(f"🔑 Password reset token generated for {email}: {token}")
            flash(f'Link di reset generato per {user["nome"]}! Usa il link qui sotto per reimpostare la password.', 'success')
        else:
            flash('Se l\'email esiste nel sistema, riceverai un link di reset.', 'info')
            print(f"⚠️ Password reset requested for non-existent email: {email}")
    
    return render_template('forgot_password.html', reset_link=reset_link)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@csrf_protect
def reset_password(token):
    token_record = db_manager.query('''
        SELECT prt.id, prt.user_id, prt.expires_at, prt.used, u.email, u.nome
        FROM password_reset_tokens prt
        JOIN utenti u ON prt.user_id = u.id
        WHERE prt.token = %s
    ''', (token,), one=True)
    
    if not token_record:
        print(f"❌ Invalid reset token: {token}")
        return render_template('reset_password.html', token_valid=False)
    
    if token_record['used']:
        print(f"❌ Token already used: {token}")
        flash('Questo link di reset è già stato utilizzato.', 'warning')
        return render_template('reset_password.html', token_valid=False)
    
    if token_record['expires_at'] < datetime.utcnow():
        print(f"❌ Token expired: {token}")
        flash('Questo link di reset è scaduto.', 'warning')
        return render_template('reset_password.html', token_valid=False)
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Le password non corrispondono.', 'error')
            return render_template('reset_password.html', token_valid=True)
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(f'Password non valida: {message}', 'error')
            return render_template('reset_password.html', token_valid=True)
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        db_manager.execute(
            'UPDATE utenti SET password = %s WHERE id = %s',
            (hashed_password, token_record['user_id'])
        )
        
        db_manager.execute(
            'UPDATE password_reset_tokens SET used = TRUE WHERE id = %s',
            (token_record['id'],)
        )
        
        print(f"✅ Password reset successful for user: {token_record['email']}")
        flash('Password reimpostata con successo! Ora puoi accedere con la nuova password.', 'success')
        return redirect('/login')
    
    return render_template('reset_password.html', token_valid=True)
