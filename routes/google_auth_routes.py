import json
import os
import requests
from flask import Blueprint, redirect, request, session, flash, url_for
from oauthlib.oauth2 import WebApplicationClient
from database_manager import db_manager

google_auth_bp = Blueprint('google_auth', __name__)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_redirect_uri():
    if os.environ.get("REPLIT_DEV_DOMAIN"):
        return f'https://{os.environ["REPLIT_DEV_DOMAIN"]}/google_login/callback'
    elif os.environ.get("REPLIT_DEPLOYMENT_ID"):
        return f'https://{os.environ.get("REPLIT_DOMAINS", "").split(",")[0]}/google_login/callback'
    return 'http://localhost:5000/google_login/callback'

if GOOGLE_CLIENT_ID:
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
    redirect_uri = get_redirect_uri()
    print(f"""
================================================================================
GOOGLE OAUTH SETUP - Aggiungi questo URL in Google Cloud Console:
Authorized redirect URI: {redirect_uri}
================================================================================
""")
else:
    client = None
    print("⚠️ Google OAuth non configurato - GOOGLE_OAUTH_CLIENT_ID mancante")


@google_auth_bp.route("/google_login")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Login con Google non configurato. Contatta l\'amministratore.', 'error')
        return redirect('/login')
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL, timeout=10).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        redirect_uri = request.base_url.replace("http://", "https://") + "/callback"
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        print(f"❌ Google OAuth error: {e}")
        flash('Errore durante il login con Google. Riprova.', 'error')
        return redirect('/login')


@google_auth_bp.route("/google_login/callback")
def google_callback():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Login con Google non configurato.', 'error')
        return redirect('/login')
    
    code = request.args.get("code")
    if not code:
        flash('Autorizzazione Google non ricevuta.', 'error')
        return redirect('/login')
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL, timeout=10).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        redirect_uri = request.base_url.replace("http://", "https://")
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=redirect_uri,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
            timeout=10
        )
        
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body, timeout=10)
        
        userinfo = userinfo_response.json()
        
        if not userinfo.get("email_verified"):
            flash('Email Google non verificata.', 'error')
            return redirect('/login')
        
        google_email = userinfo["email"]
        google_name = userinfo.get("given_name", "Utente")
        google_family_name = userinfo.get("family_name", "")
        google_picture = userinfo.get("picture", "")
        
        user = db_manager.query(
            "SELECT * FROM utenti WHERE email = %s AND attivo = true",
            (google_email,),
            one=True
        )
        
        if user:
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
            
            flash(f'Bentornato, {user["nome"]}!', 'success')
            return redirect('/dashboard')
        else:
            session['google_pending_registration'] = {
                'email': google_email,
                'nome': google_name,
                'cognome': google_family_name,
                'picture': google_picture
            }
            flash('Account non trovato. Completa la registrazione.', 'info')
            return redirect('/register?from_google=1')
            
    except Exception as e:
        print(f"❌ Google OAuth callback error: {e}")
        flash('Errore durante l\'autenticazione con Google.', 'error')
        return redirect('/login')
