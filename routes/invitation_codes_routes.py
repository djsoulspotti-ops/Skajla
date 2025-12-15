"""
Route per gestione codici invito SKAJLA
Admin può generare e inviare codici a studenti/docenti
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session
from functools import wraps
from services.invitation_codes_manager import invitation_codes_manager

invitation_codes_bp = Blueprint('invitation_codes', __name__)


def admin_required(f):
    """Decorator per verificare ruolo admin o dirigente"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Accesso non autorizzato', 'error')
            return redirect(url_for('auth.login'))
        
        user_role = session.get('ruolo', '')
        if user_role not in ['admin', 'dirigente']:
            flash('Non hai i permessi per questa operazione', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


@invitation_codes_bp.route('/admin/invitations')
@admin_required
def admin_invitations_dashboard():
    """Dashboard gestione codici invito"""
    school_id = session.get('scuola_id')
    
    if not school_id:
        flash('Nessuna scuola associata al tuo account', 'error')
        return redirect(url_for('dashboard'))
    
    codes = invitation_codes_manager.get_school_invitation_codes(school_id)
    stats = invitation_codes_manager.get_school_license_stats(school_id)
    
    user = {
        'id': session.get('user_id'),
        'nome': session.get('nome'),
        'cognome': session.get('cognome'),
        'ruolo': session.get('ruolo'),
        'scuola_id': school_id
    }
    
    return render_template('admin_invitations.html',
                          user=user,
                          codes=codes,
                          stats=stats)


@invitation_codes_bp.route('/api/invitations/generate', methods=['POST'])
@admin_required
def api_generate_codes():
    """API per generare nuovi codici invito"""
    try:
        data = request.get_json()
        
        school_id = session.get('scuola_id')
        user_id = session.get('user_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'Nessuna scuola associata'}), 400
        
        count = data.get('count', 1)
        role = data.get('role', 'studente')
        package_name = data.get('package_name', '')
        expires_days = data.get('expires_days', 30)
        
        if count < 1 or count > 100:
            return jsonify({'success': False, 'error': 'Numero codici non valido (1-100)'}), 400
        
        if role not in ['studente', 'professore']:
            return jsonify({'success': False, 'error': 'Ruolo non valido'}), 400
        
        result = invitation_codes_manager.generate_invitation_codes(
            school_id=school_id,
            count=count,
            role=role,
            created_by=user_id,
            package_name=package_name,
            expires_days=expires_days
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@invitation_codes_bp.route('/api/invitations/assign', methods=['POST'])
@admin_required
def api_assign_code():
    """API per assegnare codice a email e inviare"""
    try:
        data = request.get_json()
        
        code = data.get('code', '').strip()
        email = data.get('email', '').strip()
        send_email = data.get('send_email', True)
        
        if not code or not email:
            return jsonify({'success': False, 'error': 'Codice e email richiesti'}), 400
        
        result = invitation_codes_manager.assign_code_to_email(code, email)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        if send_email:
            from database_manager import db_manager
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT nome FROM scuole WHERE id = %s', (result['school_id'],))
                school_row = cursor.fetchone()
                school_name = school_row[0] if school_row else 'Scuola'
            
            email_result = invitation_codes_manager.send_invitation_email(
                email=email,
                code=result['code'],
                temp_password=result['temp_password'],
                school_name=school_name,
                role=result['role']
            )
            
            result['email_sent'] = email_result.get('success', False)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@invitation_codes_bp.route('/api/invitations/bulk-send', methods=['POST'])
@admin_required
def api_bulk_send():
    """API per generare e inviare codici a lista email"""
    try:
        data = request.get_json()
        
        school_id = session.get('scuola_id')
        user_id = session.get('user_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'Nessuna scuola associata'}), 400
        
        emails = data.get('emails', [])
        role = data.get('role', 'studente')
        package_name = data.get('package_name', '')
        
        if not emails:
            return jsonify({'success': False, 'error': 'Lista email vuota'}), 400
        
        if len(emails) > 100:
            return jsonify({'success': False, 'error': 'Massimo 100 email alla volta'}), 400
        
        from database_manager import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM scuole WHERE id = %s', (school_id,))
            school_row = cursor.fetchone()
            school_name = school_row[0] if school_row else 'Scuola'
        
        results = []
        for email in emails:
            email = email.strip().lower()
            if not email:
                continue
            
            gen_result = invitation_codes_manager.generate_invitation_codes(
                school_id=school_id,
                count=1,
                role=role,
                created_by=user_id,
                package_name=package_name
            )
            
            if gen_result.get('success') and gen_result.get('codes'):
                code_data = gen_result['codes'][0]
                
                assign_result = invitation_codes_manager.assign_code_to_email(
                    code_data['code'], email
                )
                
                if assign_result.get('success'):
                    email_result = invitation_codes_manager.send_invitation_email(
                        email=email,
                        code=code_data['code'],
                        temp_password=code_data['temp_password'],
                        school_name=school_name,
                        role=role
                    )
                    
                    results.append({
                        'email': email,
                        'code': code_data['code'],
                        'sent': email_result.get('success', False)
                    })
        
        return jsonify({
            'success': True,
            'total': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@invitation_codes_bp.route('/api/invitations/validate', methods=['POST'])
def api_validate_code():
    """API pubblica per validare codice durante registrazione"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'valid': False, 'error': 'Codice richiesto'}), 400
        
        result = invitation_codes_manager.validate_invitation_code(code)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500


@invitation_codes_bp.route('/api/invitations/stats')
@admin_required
def api_get_stats():
    """API per ottenere statistiche licenze"""
    try:
        school_id = session.get('scuola_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'Nessuna scuola associata'}), 400
        
        stats = invitation_codes_manager.get_school_license_stats(school_id)
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@invitation_codes_bp.route('/api/invitations/list')
@admin_required
def api_list_codes():
    """API per ottenere lista codici"""
    try:
        school_id = session.get('scuola_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'Nessuna scuola associata'}), 400
        
        status = request.args.get('status')
        role = request.args.get('role')
        
        codes = invitation_codes_manager.get_school_invitation_codes(
            school_id=school_id,
            status=status,
            role=role
        )
        
        return jsonify({'success': True, 'codes': codes})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
