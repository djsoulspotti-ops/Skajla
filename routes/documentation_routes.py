
from flask import Blueprint, render_template, send_file, abort
import os

documentation_bp = Blueprint('documentation', __name__)

@documentation_bp.route('/documentation')
def documentation_page():
    """Pagina principale documentazione"""
    return render_template('documentation.html')

@documentation_bp.route('/documentation/download/<filename>')
def download_documentation(filename):
    """Download file documentazione"""
    # Percorso sicuro per i file di documentazione
    docs_folder = os.path.join(os.getcwd(), 'static', 'docs')
    
    # Whitelist file consentiti
    allowed_files = {
        'compliance': 'INTRODUZIONE COMPLIANCE.docx',
        'guida_utente': 'GUIDA_UTENTE_SKAJLA.pdf',
        'privacy_policy': 'PRIVACY_POLICY.pdf',
        'termini_servizio': 'TERMINI_SERVIZIO.pdf'
    }
    
    if filename not in allowed_files:
        abort(404)
    
    file_path = os.path.join(docs_folder, allowed_files[filename])
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True)
