"""
OAuth Routes for SKAILA
Gestisce login/callback per Google e Microsoft OAuth
"""

from flask import Blueprint, redirect, url_for, session, flash, request
import logging
import os

logger = logging.getLogger(__name__)

# Creeremo il blueprint ma l'oauth_manager verrà inizializzato dopo
oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')


def init_oauth_routes(app, oauth_manager, db_manager):
    """
    Inizializza le route OAuth con dipendenze
    
    Args:
        app: Flask app instance
        oauth_manager: Istanza OAuthManager
        db_manager: DatabaseManager per operazioni DB
    """
    
    @oauth_bp.route('/login/<provider>')
    def oauth_login(provider):
        """
        Inizia il flow OAuth per il provider specificato
        
        Args:
            provider: 'google' o 'microsoft'
        """
        if provider not in ['google', 'microsoft']:
            flash('Provider OAuth non supportato', 'error')
            return redirect(url_for('auth.login'))
        
        # Verifica se il provider è abilitato
        if provider == 'google' and not oauth_manager.is_google_enabled():
            flash('Login con Google non configurato. Contatta l\'amministratore.', 'error')
            return redirect(url_for('auth.login'))
        
        if provider == 'microsoft' and not oauth_manager.is_microsoft_enabled():
            flash('Login con Microsoft non configurato. Contatta l\'amministratore.', 'error')
            return redirect(url_for('auth.login'))
        
        # Costruisci redirect URI dinamicamente
        # Usa REPLIT_DOMAINS se disponibile, altrimenti fallback localhost
        domain = os.getenv('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]
        
        if 'localhost' in domain:
            redirect_uri = f"http://{domain}/oauth/{provider}/callback"
        else:
            redirect_uri = f"https://{domain}/oauth/{provider}/callback"
        
        # Salva provider in session per callback
        session['oauth_provider'] = provider
        
        # Ottieni client OAuth
        if provider == 'google':
            client = oauth_manager.get_google_client()
        else:
            client = oauth_manager.get_microsoft_client()
        
        # Redirect a provider OAuth
        return client.authorize_redirect(redirect_uri)
    
    @oauth_bp.route('/<provider>/callback')
    def oauth_callback(provider):
        """
        Callback OAuth dopo autenticazione provider
        
        Args:
            provider: 'google' o 'microsoft'
        """
        try:
            # Verifica che il provider sia lo stesso della session
            if session.get('oauth_provider') != provider:
                flash('Errore di sicurezza: provider mismatch', 'error')
                return redirect(url_for('auth.login'))
            
            # Ottieni client OAuth
            if provider == 'google':
                client = oauth_manager.get_google_client()
            else:
                client = oauth_manager.get_microsoft_client()
            
            # Scambia authorization code per token
            token = client.authorize_access_token()
            
            # Ottieni informazioni utente
            user_info = oauth_manager.get_user_info(provider, token)
            
            # Verifica email verificata
            if not user_info.get('email_verified', False):
                flash('Email non verificata. Verifica la tua email con il provider OAuth.', 'error')
                return redirect(url_for('auth.login'))
            
            # Cerca o crea utente nel database
            user = _find_or_create_oauth_user(db_manager, user_info)
            
            if not user:
                flash('Errore durante la creazione dell\'account. Riprova.', 'error')
                return redirect(url_for('auth.login'))
            
            # Login utente usando session di SKAILA (no Flask-Login)
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['ruolo'] = user['ruolo']
            session['nome'] = user['nome']
            session['cognome'] = user['cognome']
            
            # Flash success message
            provider_name = 'Google' if provider == 'google' else 'Microsoft'
            flash(f'Benvenuto! Login effettuato con {provider_name}', 'success')
            
            # Clean session
            session.pop('oauth_provider', None)
            
            # Redirect a dashboard
            return redirect('/dashboard')
        
        except Exception as e:
            logger.error(f"Errore OAuth callback ({provider}): {e}")
            flash(f'Errore durante il login con {provider.capitalize()}. Riprova.', 'error')
            session.pop('oauth_provider', None)
            return redirect(url_for('auth.login'))
    
    def _find_or_create_oauth_user(db_manager, user_info):
        """
        Cerca utente esistente o crea nuovo utente da OAuth
        
        Args:
            db_manager: DatabaseManager instance
            user_info: Dizionario con dati utente da OAuth
        
        Returns:
            User object o None
        """
        try:
            email = user_info['email']
            provider = user_info['provider']
            oauth_id = user_info['oauth_id']
            
            # Cerca utente per email
            query = "SELECT * FROM utenti WHERE email = %s LIMIT 1"
            result = db_manager.execute_query(query, (email,))
            
            if result and len(result) > 0:
                # Utente esistente - aggiorna oauth info se mancante
                user = result[0]
                
                if not user.get('oauth_provider'):
                    update_query = """
                        UPDATE utenti 
                        SET oauth_provider = %s, oauth_id = %s 
                        WHERE id = %s
                    """
                    db_manager.execute_update(update_query, (provider, oauth_id, user['id']))
                    logger.info(f"✅ OAuth info aggiornate per utente {email}")
                
                # Ritorna user dict per session
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'ruolo': user['ruolo'],
                    'nome': user.get('nome', ''),
                    'cognome': user.get('cognome', '')
                }
            
            else:
                # Nuovo utente - crealo
                username = email.split('@')[0]  # Usa parte email come username
                nome = user_info.get('nome', '')
                cognome = user_info.get('cognome', '')
                
                insert_query = """
                    INSERT INTO utenti (username, email, nome, cognome, ruolo, oauth_provider, oauth_id, email_verified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                result = db_manager.execute_query(
                    insert_query,
                    (username, email, nome, cognome, 'studente', provider, oauth_id, True)
                )
                
                if result and len(result) > 0:
                    new_user_id = result[0]['id']
                    logger.info(f"✅ Nuovo utente OAuth creato: {email} (ID: {new_user_id})")
                    
                    # Ritorna user dict per session
                    return {
                        'id': new_user_id,
                        'username': username,
                        'email': email,
                        'ruolo': 'studente',
                        'nome': nome,
                        'cognome': cognome
                    }
                else:
                    return None
        
        except Exception as e:
            logger.error(f"Errore find_or_create_oauth_user: {e}")
            return None
    
    # Registra blueprint
    app.register_blueprint(oauth_bp)
    logger.info("✅ OAuth routes registrate")
