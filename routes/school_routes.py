# Route per auto-registrazione scuole e sistema dirigenti
from flask import Blueprint, request, render_template, redirect, flash, session, url_for
from school_system import school_system
from services.auth_service import auth_service
from database_manager import db_manager
from csrf_protection import csrf_protect
import json

school_bp = Blueprint('school', __name__)

@school_bp.route('/schools/register', methods=['GET', 'POST'])
@csrf_protect
def auto_register_school():
    """Auto-registrazione scuola con verifica email dirigente"""
    if request.method == 'POST':
        try:
            nome_scuola = request.form['nome_scuola'].strip()
            dominio_email = request.form['dominio_email'].strip().lower()
            dirigente_email = request.form['dirigente_email'].strip().lower()
            dirigente_nome = request.form['dirigente_nome'].strip()
            dirigente_cognome = request.form['dirigente_cognome'].strip()
            
            # Validazioni base
            if not all([nome_scuola, dominio_email, dirigente_email, dirigente_nome, dirigente_cognome]):
                flash('Tutti i campi sono obbligatori', 'error')
                return render_template('auto_register_school.html')
            
            # Verifica che l'email dirigente sia del dominio scuola
            if not dirigente_email.endswith(f'@{dominio_email}'):
                flash(f'L\'email del dirigente deve essere del dominio {dominio_email}', 'error')
                return render_template('auto_register_school.html')
            
            # Auto-registrazione scuola
            result = school_system.register_school_auto(
                nome_scuola, dominio_email, dirigente_email, 
                dirigente_nome, dirigente_cognome
            )
            
            if result['success']:
                # In ambiente reale, qui invieresti l'email
                # Per ora mostriamo il link di verifica
                verification_url = url_for('school.verify_email', 
                                         token=result['verification_token'], 
                                         _external=True)
                
                flash(f'Scuola registrata! Email di verifica inviata a {dirigente_email}', 'success')
                flash(f'Link di verifica (demo): {verification_url}', 'info')
                return redirect('/schools/register')
            else:
                flash(result['message'], 'error')
                
        except Exception as e:
            flash(f'Errore durante la registrazione: {str(e)}', 'error')
    
    return render_template('auto_register_school.html')

@school_bp.route('/verify')
def verify_email():
    """Verifica email dirigente e attiva scuola"""
    token = request.args.get('token')
    
    if not token:
        flash('Token di verifica mancante', 'error')
        return redirect('/')
    
    # Verifica token e attiva scuola
    result = school_system.verify_dirigente_email(token)
    
    if result['success']:
        # Genera token sicuro per setup account dirigente
        setup_token = school_system.generate_secure_token()
        
        # Salva token per setup account
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(hours=48)
            
            if db_manager.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO email_verifications 
                    (email, purpose, token, expires_at, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (result['email'], 'dirigente_account_setup', setup_token, 
                      expires_at, json.dumps({"school_id": result["school_id"], "nome": result["dirigente_nome"], "cognome": result["dirigente_cognome"]})))
            else:
                cursor.execute('''
                    INSERT INTO email_verifications 
                    (email, purpose, token, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (result['email'], 'dirigente_account_setup', setup_token, 
                      expires_at, json.dumps({"school_id": result["school_id"], "nome": result["dirigente_nome"], "cognome": result["dirigente_cognome"]})))
            conn.commit()
        
        # Link sicuro per setup account dirigente
        setup_url = url_for('school.setup_dirigente_account', 
                           token=setup_token, _external=True)
        
        flash('Scuola attivata con successo!', 'success')
        flash(f'Link setup account dirigente (48h): {setup_url}', 'info')
            
        return redirect('/login')
    else:
        flash(result['message'], 'error')
        return redirect('/')

@school_bp.route('/dashboard/dirigente')
def dirigente_dashboard():
    """Dashboard dirigente per gestione codici"""
    if 'user_id' not in session:
        flash('Accesso non autorizzato', 'error')
        return redirect('/login')
    
    # SECURITY: Solo dirigenti possono accedere
    if session.get('ruolo') != 'dirigente':
        flash('Accesso riservato solo ai dirigenti', 'error')
        return redirect('/dashboard')
    
    user_id = session['user_id']
    scuola_id = session.get('scuola_id')
    
    if not scuola_id:
        flash('Scuola non associata', 'error')
        return redirect('/dashboard')
    
    # Ottieni codici scuola
    codes_result = school_system.get_school_codes(scuola_id, user_id)
    
    if not codes_result['success']:
        flash(codes_result['message'], 'error')
        return redirect('/dashboard')
    
    return render_template('dirigente_dashboard.html', 
                         school_data=codes_result)

@school_bp.route('/setup_account', methods=['GET', 'POST'])
@csrf_protect
def setup_dirigente_account():
    """Setup sicuro account dirigente"""
    token = request.args.get('token') or request.form.get('token')
    
    if not token:
        flash('Token di setup mancante', 'error')
        return redirect('/')
    
    # Verifica token setup dirigente
    if db_manager.db_type == 'postgresql':
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT email, metadata FROM email_verifications 
                WHERE token = %s AND purpose = 'dirigente_account_setup' 
                AND expires_at > NOW() AND consumed_at IS NULL
            ''', (token,))
            result = cursor.fetchone()
    else:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT email, metadata FROM email_verifications 
                WHERE token = ? AND purpose = 'dirigente_account_setup' 
                AND expires_at > datetime('now') AND consumed_at IS NULL
            ''', (token,))
            result = cursor.fetchone()
    
    if not result:
        flash('Token di setup non valido o scaduto', 'error')
        return redirect('/')
    
    email, metadata = result
    # Handle metadata parsing for cross-DB compatibility (PostgreSQL JSONB vs SQLite TEXT)
    if isinstance(metadata, (dict, list)):
        setup_data = metadata  # PostgreSQL already returns dict/list
    else:
        setup_data = json.loads(metadata)  # SQLite returns string
    
    if request.method == 'POST':
        # Processo POST - completa setup account dirigente
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            # Validazioni
            if not username or not password:
                flash('Username e password sono obbligatori', 'error')
                return render_template('setup_dirigente.html', setup_data=setup_data, token=token)
            
            if password != confirm_password:
                flash('Le password non corrispondono', 'error')
                return render_template('setup_dirigente.html', setup_data=setup_data, token=token)
            
            # Crea account dirigente
            result = auth_service.create_user(
                username=username,
                email=email,
                password=password,
                nome=setup_data['nome'],
                cognome=setup_data['cognome'],
                ruolo='dirigente',
                classe_nome=None,
                scuola_id=setup_data['school_id'],
                classe_id=None
            )
            
            if result['success']:
                # Consuma token di setup
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    from datetime import datetime
                    consumed_at = datetime.now()
                    
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('''
                            UPDATE email_verifications 
                            SET consumed_at = %s 
                            WHERE token = %s AND purpose = 'dirigente_account_setup'
                        ''', (consumed_at, token))
                    else:
                        cursor.execute('''
                            UPDATE email_verifications 
                            SET consumed_at = ? 
                            WHERE token = ? AND purpose = 'dirigente_account_setup'
                        ''', (consumed_at, token))
                    conn.commit()
                
                flash('Account dirigente creato con successo! Effettua il login.', 'success')
                return redirect('/login')
            else:
                flash(result['message'], 'error')
                return render_template('setup_dirigente.html', setup_data=setup_data, token=token)
                
        except Exception as e:
            flash(f'Errore durante la creazione dell\'account: {str(e)}', 'error')
            return render_template('setup_dirigente.html', setup_data=setup_data, token=token)
    
    # GET - Mostra form setup dirigente  
    return render_template('setup_dirigente.html', 
                         setup_data=setup_data, 
                         token=token)

@school_bp.route('/dashboard/dirigente/generate_personal_codes', methods=['POST'])
@csrf_protect
def generate_personal_codes():
    """Genera codici personali per ogni persona della scuola"""
    if 'user_id' not in session:
        flash('Accesso non autorizzato', 'error')
        return redirect('/login')
    
    # SECURITY: Solo dirigenti possono generare codici personali
    if session.get('ruolo') != 'dirigente':
        flash('Accesso riservato solo ai dirigenti', 'error')
        return redirect('/dashboard')
    
    user_id = session['user_id']
    scuola_id = session.get('scuola_id')
    
    # Implementa sistema codici personali automatico
    result = school_system.generate_personal_codes_for_school(scuola_id, user_id)
    
    if result['success']:
        flash(f'Generati {result["codes_count"]} codici personali!', 'success')
        flash('Email automatiche inviate a tutti gli utenti', 'info')
    else:
        flash(result['message'], 'error')
    
    return redirect('/dashboard/dirigente')