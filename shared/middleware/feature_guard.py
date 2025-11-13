"""
SKAILA - Feature Guard Middleware
CRITICO: Blocca accesso alle route quando feature è disabilitata
"""

from functools import wraps
from flask import session, redirect, flash, jsonify, request
from services.tenant_guard import get_current_school_id
from services.school.school_features_manager import school_features_manager
from shared.error_handling import AuthorizationError, DatabaseError

def require_feature(feature_name):
    """
    Decorator per proteggere route che richiedono una feature abilitata
    
    Usage:
        @app.route('/registro')
        @require_login
        @require_feature('registro_elettronico')
        def registro():
            ...
    
    Args:
        feature_name: Nome della feature richiesta (es. 'gamification', 'registro_elettronico')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verifica autenticazione
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Non autorizzato'}), 401
                return redirect('/login')
            
            # Ottieni school_id
            try:
                school_id = get_current_school_id()
            except Exception as e:
                if request.is_json:
                    return jsonify({'error': 'Errore identificazione scuola'}), 500
                return redirect('/dashboard')
            
            # Verifica feature abilitata
            if not school_features_manager.is_feature_enabled(school_id, feature_name):
                # Feature disabilitata
                if request.is_json:
                    return jsonify({
                        'error': 'Feature non disponibile',
                        'message': f'La funzionalità {feature_name} non è disponibile per la tua scuola. Contatta l\'amministratore.',
                        'feature': feature_name,
                        'upgrade_required': True
                    }), 403
                
                # Web request - redirect con messaggio
                flash(f'⚠️ Funzionalità non disponibile. La tua scuola non ha accesso a {feature_name}.', 'warning')
                return redirect('/dashboard')
            
            # Feature abilitata - procedi
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_feature_enabled(school_id, feature_name):
    """
    Helper function per verificare se una feature è abilitata (uso in codice)
    
    Args:
        school_id: ID della scuola
        feature_name: Nome della feature
    
    Returns:
        bool: True se abilitata, False altrimenti
    """
    return school_features_manager.is_feature_enabled(school_id, feature_name)


def require_feature_or_raise(school_id, feature_name):
    """
    Verifica che una feature sia abilitata, altrimenti solleva AuthorizationError
    
    Args:
        school_id: ID della scuola
        feature_name: Nome della feature
    
    Raises:
        AuthorizationError: Se la feature non è abilitata
        
    Usage in API routes with @handle_errors decorator:
        try:
            require_feature_or_raise(school_id, Features.AI_COACH)
        except AuthorizationError:
            raise  # Let handle_errors decorator normalize response
    """
    if not school_features_manager.is_feature_enabled(school_id, feature_name):
        raise AuthorizationError(
            message=f'Feature {feature_name} non disponibile per questa scuola',
            user_message=f'La funzionalità {feature_name} non è disponibile. Contatta l\'amministratore.',
            context={
                'school_id': school_id,
                'feature': feature_name,
                'upgrade_required': True
            }
        )


# Feature name constants per evitare typo
class Features:
    GAMIFICATION = 'gamification'
    AI_COACH = 'ai_coach'
    REGISTRO = 'registro_elettronico'
    MATERIALI = 'materiali_didattici'
    SKAILA_CONNECT = 'skaila_connect'
    CALENDARIO = 'calendario'
    ANALYTICS = 'analytics'
