"""
SKAJLA - Static Routes
Routes for static pages (Home, Contacts, Team, etc.)
"""

from flask import Blueprint, render_template, session, redirect, make_response, request, jsonify
from services.database.database_manager import db_manager
from config import config

static_bp = Blueprint('static_routes', __name__)

@static_bp.route('/', methods=['GET', 'HEAD'])
def index():
    # Fast path for health check probes (Autoscale, load balancers)
    from flask import request
    if request.method == 'HEAD' or \
       'GoogleHC' in request.headers.get('User-Agent', '') or \
       'kube-probe' in request.headers.get('User-Agent', '') or \
       'Replit' in request.headers.get('User-Agent', ''):
        return '', 200
    
    if 'user_id' in session:
        return redirect('/dashboard')
    
    # Statistiche pubbliche per la homepage
    try:
        total_users = db_manager.query('''
            SELECT COUNT(*) as count FROM utenti WHERE attivo = true
        ''', one=True)
        
        total_schools = db_manager.query('''
            SELECT COUNT(*) as count FROM scuole WHERE attiva = true
        ''', one=True)
        
        total_students = db_manager.query('''
            SELECT COUNT(*) as count FROM utenti WHERE ruolo = 'studente' AND attivo = true
        ''', one=True)
        
        ai_interactions = db_manager.query('''
            SELECT COUNT(*) as count FROM ai_conversations
        ''', one=True)
        
        stats = {
            'total_users': total_users['count'] if total_users else 0,
            'total_schools': total_schools['count'] if total_schools else 0,
            'total_students': total_students['count'] if total_students else 0,
            'ai_interactions': ai_interactions['count'] if ai_interactions else 0
        }
    except Exception as e:
        print(f"Error loading homepage stats: {e}")
        stats = {
            'total_users': 0,
            'total_schools': 0,
            'total_students': 0,
            'ai_interactions': 0
        }
    
    return render_template('index.html', stats=stats, domain=config.DOMAIN_URL)

@static_bp.route('/contatti')
def contatti():
    return render_template('contatti.html', domain=config.DOMAIN_URL)

@static_bp.route('/api/contact', methods=['POST'])
def handle_contact_form():
    """Handle contact form submission"""
    try:
        # In a real app, we would send an email here using SendGrid/SMTP
        # For now, we simulate success and could log to DB if needed
        data = request.form
        print(f"📩 New Contact Request: {data.get('email')} from {data.get('istituto')}")
        
        # Simulate processing delay
        import time
        time.sleep(1)
        
        return jsonify({'success': True, 'message': 'Richiesta inviata con successo'})
    except Exception as e:
        print(f"❌ Contact Form Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@static_bp.route('/team')
def team():
    return render_template('team.html', domain=config.DOMAIN_URL)

@static_bp.route('/gamification')
def gamification_dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    response = make_response(render_template('gamification_dashboard.html', user=session))
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
    return response

@static_bp.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page (Placeholder for now)"""
    return render_template('index.html', stats={}, domain=config.DOMAIN_URL) # Fallback to index if no template

@static_bp.route('/terms')
def terms_of_service():
    """Terms of Service page (Placeholder for now)"""
    return render_template('index.html', stats={}, domain=config.DOMAIN_URL) # Fallback to index if no template
