
"""
SKAILA - Business Intelligence Dashboard Routes
Dashboard BI per dirigenti e professori con organigrammi visuali
"""

from flask import Blueprint, render_template, session, redirect, jsonify
from database_manager import db_manager
from services.tenant_guard import get_current_school_id, TenantGuardException
from shared.middleware.auth import require_login
from datetime import datetime, timedelta

bi_bp = Blueprint('bi_dashboard', __name__, url_prefix='/bi')

@bi_bp.route('/dashboard')
@require_login
def bi_dashboard():
    """Dashboard Business Intelligence principale"""
    ruolo = session.get('ruolo')
    
    # Solo dirigenti e professori
    if ruolo not in ['dirigente', 'professore', 'admin']:
        return redirect('/dashboard')
    
    try:
        school_id = get_current_school_id()
        user_id = session['user_id']
        
        # Dati organigramma
        org_data = get_organization_tree(school_id, ruolo, user_id)
        
        # KPI Scuola
        school_kpi = get_school_kpi(school_id)
        
        # Statistiche classi
        classes_stats = get_classes_statistics(school_id, ruolo, user_id)
        
        return render_template('bi_dashboard.html',
                             user=session,
                             org_tree=org_data,
                             school_kpi=school_kpi,
                             classes_stats=classes_stats,
                             ruolo=ruolo)
    
    except TenantGuardException:
        session.clear()
        return redirect('/login')

@bi_bp.route('/api/organigramma')
@require_login
def api_organigramma():
    """API JSON per organigramma interattivo"""
    try:
        school_id = get_current_school_id()
        ruolo = session.get('ruolo')
        user_id = session['user_id']
        
        org_tree = get_organization_tree(school_id, ruolo, user_id)
        
        return jsonify({'success': True, 'data': org_tree})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/api/classe/<classe>/stats')
@require_login
def api_classe_stats(classe):
    """API statistiche dettagliate classe"""
    try:
        school_id = get_current_school_id()
        
        # Statistiche aggregate classe
        stats = db_manager.query('''
            SELECT 
                COUNT(DISTINCT u.id) as total_studenti,
                ROUND(AVG(CASE WHEN rv.voto IS NOT NULL THEN rv.voto ELSE 0 END), 2) as media_voti,
                COUNT(DISTINCT rv.id) as total_voti,
                COUNT(DISTINCT CASE WHEN rp.status = 'presente' THEN rp.id END) * 100.0 / 
                    NULLIF(COUNT(DISTINCT rp.id), 0) as tasso_presenze
            FROM utenti u
            LEFT JOIN registro_voti rv ON u.id = rv.student_id 
                AND rv.date >= CURRENT_DATE - INTERVAL '30 days'
            LEFT JOIN registro_presenze rp ON u.id = rp.student_id
                AND rp.date >= CURRENT_DATE - INTERVAL '30 days'
            WHERE u.classe = %s AND u.scuola_id = %s AND u.ruolo = 'studente'
        ''', (classe, school_id), one=True)
        
        # Distribuzione voti
        voti_dist = db_manager.query('''
            SELECT 
                rv.subject,
                COUNT(*) as count,
                ROUND(AVG(rv.voto), 2) as media
            FROM registro_voti rv
            JOIN utenti u ON rv.student_id = u.id
            WHERE u.classe = %s AND u.scuola_id = %s
                AND rv.date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY rv.subject
            ORDER BY media DESC
        ''', (classe, school_id))
        
        # Studenti per performance
        performance_levels = db_manager.query('''
            SELECT 
                CASE 
                    WHEN AVG(rv.voto) >= 8 THEN 'Eccellente'
                    WHEN AVG(rv.voto) >= 7 THEN 'Buono'
                    WHEN AVG(rv.voto) >= 6 THEN 'Sufficiente'
                    ELSE 'Insufficiente'
                END as livello,
                COUNT(DISTINCT u.id) as count
            FROM utenti u
            LEFT JOIN registro_voti rv ON u.id = rv.student_id
            WHERE u.classe = %s AND u.scuola_id = %s AND u.ruolo = 'studente'
            GROUP BY livello
        ''', (classe, school_id))
        
        return jsonify({
            'success': True,
            'stats': stats,
            'voti_per_materia': voti_dist,
            'performance_distribution': performance_levels
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/api/studente/<int:student_id>/dashboard')
@require_login
def api_studente_dashboard(student_id):
    """API dashboard studente per drill-down"""
    try:
        school_id = get_current_school_id()
        
        # Verifica accesso
        student = db_manager.query('''
            SELECT nome, cognome, classe FROM utenti 
            WHERE id = %s AND scuola_id = %s AND ruolo = 'studente'
        ''', (student_id, school_id), one=True)
        
        if not student:
            return jsonify({'success': False, 'error': 'Studente non trovato'}), 404
        
        # Media voti per materia
        voti = db_manager.query('''
            SELECT subject, ROUND(AVG(voto), 2) as media, COUNT(*) as count
            FROM registro_voti
            WHERE student_id = %s
            GROUP BY subject
            ORDER BY media DESC
        ''', (student_id,))
        
        # Presenze ultimi 30 giorni
        presenze = db_manager.query('''
            SELECT 
                COUNT(*) as totale,
                COUNT(CASE WHEN status = 'presente' THEN 1 END) as presenti,
                COUNT(CASE WHEN status = 'assente' THEN 1 END) as assenti
            FROM registro_presenze
            WHERE student_id = %s AND date >= CURRENT_DATE - INTERVAL '30 days'
        ''', (student_id,), one=True)
        
        # XP e gamification
        gamification = db_manager.query('''
            SELECT total_xp, current_level, current_streak
            FROM user_gamification
            WHERE user_id = %s
        ''', (student_id,), one=True)
        
        return jsonify({
            'success': True,
            'student': student,
            'voti_per_materia': voti,
            'presenze': presenze,
            'gamification': gamification
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def get_organization_tree(school_id, ruolo, user_id):
    """Costruisce albero organizzazione gerarchico"""
    
    # Root: Scuola
    scuola = db_manager.query('''
        SELECT nome FROM scuole WHERE id = %s
    ''', (school_id,), one=True)
    
    tree = {
        'name': scuola['nome'],
        'type': 'scuola',
        'id': school_id,
        'children': []
    }
    
    # Livello 1: Classi
    if ruolo == 'dirigente':
        # Dirigente vede tutte le classi
        classi = db_manager.query('''
            SELECT DISTINCT classe, COUNT(DISTINCT id) as studenti_count
            FROM utenti
            WHERE scuola_id = %s AND ruolo = 'studente' AND classe IS NOT NULL
            GROUP BY classe
            ORDER BY classe
        ''', (school_id,))
    else:
        # Professore vede solo sue classi (placeholder - da implementare con docenti_classi)
        classi = db_manager.query('''
            SELECT DISTINCT classe, COUNT(DISTINCT id) as studenti_count
            FROM utenti
            WHERE scuola_id = %s AND ruolo = 'studente' AND classe IS NOT NULL
            GROUP BY classe
            ORDER BY classe
        ''', (school_id,))
    
    for classe_row in classi:
        classe_name = classe_row['classe']
        
        # Statistiche classe
        classe_stats = db_manager.query('''
            SELECT 
                COUNT(DISTINCT u.id) as studenti,
                ROUND(AVG(CASE WHEN rv.voto IS NOT NULL THEN rv.voto ELSE 0 END), 2) as media_voti,
                COUNT(DISTINCT CASE WHEN rp.status = 'presente' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(DISTINCT rp.id), 0) as presenze_perc
            FROM utenti u
            LEFT JOIN registro_voti rv ON u.id = rv.student_id
            LEFT JOIN registro_presenze rp ON u.id = rp.student_id
            WHERE u.classe = %s AND u.scuola_id = %s AND u.ruolo = 'studente'
        ''', (classe_name, school_id), one=True)
        
        classe_node = {
            'name': f'Classe {classe_name}',
            'type': 'classe',
            'id': classe_name,
            'stats': classe_stats,
            'children': []
        }
        
        # Livello 2: Studenti (solo nomi, privacy)
        studenti = db_manager.query('''
            SELECT id, nome, cognome
            FROM utenti
            WHERE classe = %s AND scuola_id = %s AND ruolo = 'studente'
            ORDER BY cognome, nome
        ''', (classe_name, school_id))
        
        for studente in studenti:
            # Stats aggregate studente (no dettagli personali)
            student_stats = db_manager.query('''
                SELECT 
                    ROUND(AVG(voto), 2) as media_voti,
                    COUNT(DISTINCT date) as giorni_voti
                FROM registro_voti
                WHERE student_id = %s
            ''', (studente['id'],), one=True)
            
            studente_node = {
                'name': f"{studente['nome']} {studente['cognome'][0]}.",
                'type': 'studente',
                'id': studente['id'],
                'stats': student_stats
            }
            
            classe_node['children'].append(studente_node)
        
        tree['children'].append(classe_node)
    
    return tree


def get_school_kpi(school_id):
    """KPI principali scuola"""
    kpi = db_manager.query('''
        SELECT 
            COUNT(DISTINCT CASE WHEN ruolo = 'studente' THEN id END) as totale_studenti,
            COUNT(DISTINCT CASE WHEN ruolo = 'professore' THEN id END) as totale_professori,
            COUNT(DISTINCT classe) as totale_classi,
            ROUND(AVG(CASE WHEN ruolo = 'studente' AND EXISTS(
                SELECT 1 FROM registro_voti rv WHERE rv.student_id = utenti.id
            ) THEN (
                SELECT AVG(voto) FROM registro_voti WHERE student_id = utenti.id
            ) END), 2) as media_generale_scuola
        FROM utenti
        WHERE scuola_id = %s AND attivo = true
    ''', (school_id,), one=True)
    
    # Tasso presenze scuola (ultimi 30 giorni)
    presenze_kpi = db_manager.query('''
        SELECT 
            COUNT(*) as totale_registrazioni,
            COUNT(CASE WHEN status = 'presente' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0) as tasso_presenze
        FROM registro_presenze rp
        JOIN utenti u ON rp.student_id = u.id
        WHERE u.scuola_id = %s AND rp.date >= CURRENT_DATE - INTERVAL '30 days'
    ''', (school_id,), one=True)
    
    return {
        **kpi,
        'tasso_presenze': round(presenze_kpi['tasso_presenze'] or 0, 1)
    }


def get_classes_statistics(school_id, ruolo, user_id):
    """Statistiche dettagliate per classi"""
    
    classi_stats = db_manager.query('''
        SELECT 
            u.classe,
            COUNT(DISTINCT u.id) as studenti_count,
            ROUND(AVG(CASE WHEN rv.voto IS NOT NULL THEN rv.voto END), 2) as media_classe,
            COUNT(DISTINCT rv.id) as voti_registrati,
            COUNT(DISTINCT CASE WHEN rp.status = 'presente' THEN rp.id END) * 100.0 / 
                NULLIF(COUNT(DISTINCT rp.id), 0) as tasso_presenze
        FROM utenti u
        LEFT JOIN registro_voti rv ON u.id = rv.student_id 
            AND rv.date >= CURRENT_DATE - INTERVAL '30 days'
        LEFT JOIN registro_presenze rp ON u.id = rp.student_id
            AND rp.date >= CURRENT_DATE - INTERVAL '30 days'
        WHERE u.scuola_id = %s AND u.ruolo = 'studente' AND u.classe IS NOT NULL
        GROUP BY u.classe
        ORDER BY u.classe
    ''', (school_id,))
    
    return classi_stats
