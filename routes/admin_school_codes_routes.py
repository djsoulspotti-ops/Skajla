"""
Routes Admin per gestione codici scuole
"""

from flask import Blueprint, render_template, session, redirect, jsonify, request
from services.school_codes_manager import school_codes_manager
from functools import wraps

admin_codes_bp = Blueprint('admin_codes', __name__)

def require_admin(f):
    """Decorator per richiedere ruolo admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('ruolo') != 'admin':
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@admin_codes_bp.route('/admin/school-codes')
@require_admin
def admin_school_codes():
    """Dashboard admin per gestione codici scuole"""
    codes = school_codes_manager.get_all_codes(include_assigned=True)
    available_count = school_codes_manager.get_available_codes_count()
    
    return render_template('admin_school_codes.html', 
                         user=session,
                         codes=codes,
                         available_count=available_count,
                         total_count=len(codes))

@admin_codes_bp.route('/admin/school-codes/generate', methods=['POST'])
@require_admin
def generate_codes():
    """Genera i codici iniziali"""
    force = request.json.get('force', False) if request.is_json else False
    
    result = school_codes_manager.generate_initial_codes(force_regenerate=force)
    return jsonify(result)

@admin_codes_bp.route('/admin/school-codes/export')
@require_admin
def export_codes():
    """Esporta codici in formato testo"""
    export_text = school_codes_manager.export_codes_for_distribution()
    
    from flask import Response
    return Response(
        export_text,
        mimetype='text/plain',
        headers={
            'Content-Disposition': 'attachment; filename=skaila_codici_scuole.txt'
        }
    )

@admin_codes_bp.route('/admin/school-codes/status')
@require_admin
def codes_status():
    """API per status codici"""
    available = school_codes_manager.get_available_codes_count()
    codes = school_codes_manager.get_all_codes(include_assigned=True)
    
    return jsonify({
        'available': available,
        'total': len(codes),
        'assigned': len([c for c in codes if c['assigned']])
    })
