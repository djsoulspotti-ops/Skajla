"""
OAuth Manager for SKAILA
Gestisce autenticazione con Google e Microsoft OAuth 2.0
Usa Authlib per implementazione moderna e sicura
"""

import os
from authlib.integrations.flask_client import OAuth
from flask import url_for
import logging

logger = logging.getLogger(__name__)


class OAuthManager:
    """
    Gestore centralizzato per OAuth providers (Google, Microsoft)
    """
    
    def __init__(self, app=None):
        self.oauth = OAuth()
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inizializza OAuth providers con l'applicazione Flask"""
        self.app = app
        self.oauth.init_app(app)
        
        # Configurazione Google OAuth
        self._configure_google()
        
        # Configurazione Microsoft OAuth
        self._configure_microsoft()
        
        logger.info("✅ OAuth Manager inizializzato (Google + Microsoft)")
    
    def _configure_google(self):
        """
        Configura Google OAuth 2.0
        Usa OpenID Connect per autenticazione moderna
        """
        google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        
        if not google_client_id or not google_client_secret:
            logger.warning("⚠️ Google OAuth credentials non trovate - Login Google disabilitato")
            logger.info("""
Per abilitare Google OAuth:
1. Vai su https://console.cloud.google.com/apis/credentials
2. Crea OAuth 2.0 Client ID
3. Aggiungi redirect URI: https://YOUR_DOMAIN/oauth/google/callback
4. Imposta secrets: GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET
            """)
            return
        
        self.oauth.register(
            name='google',
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile',
                'prompt': 'select_account'  # Permette selezione account
            }
        )
        logger.info("✅ Google OAuth configurato")
    
    def _configure_microsoft(self):
        """
        Configura Microsoft OAuth 2.0 (Azure AD / Entra ID)
        Usa Microsoft Identity Platform v2.0
        """
        microsoft_client_id = os.getenv('MICROSOFT_OAUTH_CLIENT_ID')
        microsoft_client_secret = os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET')
        
        if not microsoft_client_id or not microsoft_client_secret:
            logger.warning("⚠️ Microsoft OAuth credentials non trovate - Login Microsoft disabilitato")
            logger.info("""
Per abilitare Microsoft OAuth:
1. Vai su https://entra.microsoft.com/
2. App registrations → New registration
3. Aggiungi redirect URI: https://YOUR_DOMAIN/oauth/microsoft/callback
4. Certificates & secrets → New client secret
5. Imposta secrets: MICROSOFT_OAUTH_CLIENT_ID e MICROSOFT_OAUTH_CLIENT_SECRET
            """)
            return
        
        self.oauth.register(
            name='microsoft',
            client_id=microsoft_client_id,
            client_secret=microsoft_client_secret,
            authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            authorize_params=None,
            access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
            access_token_params=None,
            refresh_token_url=None,
            client_kwargs={
                'scope': 'openid email profile User.Read',
                'prompt': 'select_account'
            }
        )
        logger.info("✅ Microsoft OAuth configurato")
    
    def get_google_client(self):
        """Ritorna client OAuth per Google"""
        return self.oauth.google
    
    def get_microsoft_client(self):
        """Ritorna client OAuth per Microsoft"""
        return self.oauth.microsoft
    
    def is_google_enabled(self):
        """Verifica se Google OAuth è abilitato"""
        return (os.getenv('GOOGLE_OAUTH_CLIENT_ID') and 
                os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'))
    
    def is_microsoft_enabled(self):
        """Verifica se Microsoft OAuth è abilitato"""
        return (os.getenv('MICROSOFT_OAUTH_CLIENT_ID') and 
                os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET'))
    
    async def exchange_code_for_token(self, provider, code, redirect_uri):
        """
        Scambia authorization code per access token
        
        Args:
            provider: 'google' o 'microsoft'
            code: Authorization code ricevuto dal callback
            redirect_uri: URI di redirect registrato
        
        Returns:
            dict: Token data con access_token, id_token, etc.
        """
        if provider == 'google':
            client = self.get_google_client()
        elif provider == 'microsoft':
            client = self.get_microsoft_client()
        else:
            raise ValueError(f"Provider non supportato: {provider}")
        
        token = await client.authorize_access_token()
        return token
    
    def get_user_info(self, provider, token):
        """
        Ottiene informazioni utente dal provider OAuth
        
        Args:
            provider: 'google' o 'microsoft'
            token: Access token ottenuto
        
        Returns:
            dict: Dati utente normalizzati {email, nome, cognome, picture}
        """
        if provider == 'google':
            return self._get_google_user_info(token)
        elif provider == 'microsoft':
            return self._get_microsoft_user_info(token)
        else:
            raise ValueError(f"Provider non supportato: {provider}")
    
    def _get_google_user_info(self, token):
        """Estrae user info da Google OAuth token"""
        try:
            # Google usa OpenID Connect, quindi il token contiene id_token
            user_info = self.oauth.google.parse_id_token(token)
            
            return {
                'email': user_info.get('email'),
                'email_verified': user_info.get('email_verified', False),
                'nome': user_info.get('given_name', ''),
                'cognome': user_info.get('family_name', ''),
                'picture': user_info.get('picture'),
                'provider': 'google',
                'oauth_id': user_info.get('sub')  # Google unique ID
            }
        except Exception as e:
            logger.error(f"Errore parsing Google user info: {e}")
            raise
    
    def _get_microsoft_user_info(self, token):
        """Estrae user info da Microsoft Graph API"""
        try:
            # Microsoft richiede chiamata a Graph API
            resp = self.oauth.microsoft.get(
                'https://graph.microsoft.com/v1.0/me',
                token=token
            )
            user_data = resp.json()
            
            # Microsoft non ha campo "nome" e "cognome" separati di default
            nome_completo = user_data.get('displayName', '').split(' ', 1)
            nome = nome_completo[0] if len(nome_completo) > 0 else ''
            cognome = nome_completo[1] if len(nome_completo) > 1 else ''
            
            return {
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'email_verified': True,  # Microsoft verifica sempre email
                'nome': nome,
                'cognome': cognome,
                'picture': None,  # Microsoft Graph richiede chiamata separata per foto
                'provider': 'microsoft',
                'oauth_id': user_data.get('id')  # Microsoft unique ID
            }
        except Exception as e:
            logger.error(f"Errore parsing Microsoft user info: {e}")
            raise


# Istanza globale
oauth_manager = OAuthManager()
