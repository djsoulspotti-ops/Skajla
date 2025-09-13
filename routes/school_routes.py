# Route per auto-registrazione scuole e sistema dirigenti
from flask import Blueprint, request, render_template, redirect, flash, session, url_for
from school_system import school_system
from services.auth_service import auth_service

school_bp = Blueprint('school', __name__)

@school_bp.route('/schools/register', methods=['GET', 'POST'])
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
        # Crea automaticamente utente dirigente
        dirigente_result = auth_service.create_user(
            username=f"dirigente_{result['school_id']}",
            email=result['email'],
            password="temp_password_123", # Password temporanea
            nome=result['dirigente_nome'],
            cognome=result['dirigente_cognome'],
            ruolo='dirigente',
            classe_nome='',
            scuola_id=result['school_id'],
            classe_id=None
        )
        
        if dirigente_result['success']:
            flash('Scuola attivata con successo! Il dirigente può ora accedere.', 'success')
            flash('Username temporaneo: dirigente_' + str(result['school_id']), 'info')
            flash('Password temporanea: temp_password_123 (cambiarla al primo accesso)', 'warning')
        else:
            flash('Scuola attivata ma errore nella creazione utente dirigente', 'warning')
            
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

@school_bp.route('/dashboard/dirigente/regenerate_codes', methods=['POST'])
def regenerate_teacher_codes():
    """Rigenera codici docenti (solo dirigenti)"""
    if 'user_id' not in session or session.get('ruolo') != 'dirigente':
        flash('Accesso non autorizzato', 'error')
        return redirect('/login')
    
    user_id = session['user_id']
    scuola_id = session.get('scuola_id')
    
    # TODO: Implementa rigenerazione codici
    flash('Funzionalità di rigenerazione in arrivo', 'info')
    return redirect('/dashboard/dirigente')