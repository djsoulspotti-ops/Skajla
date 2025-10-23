"""
SKAILA - Admin Reports Routes
Gestione report aziendali automatici
"""

from flask import Blueprint, render_template, session, redirect, jsonify, send_file
from database_manager import db_manager
from report_generator import report_generator
from report_scheduler import report_scheduler
import json
from datetime import datetime

admin_reports_bp = Blueprint('admin_reports', __name__, url_prefix='/admin/reports')

@admin_reports_bp.route('/')
def reports_dashboard():
    """Dashboard report con storico"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return redirect('/login')
    
    try:
        # Recupera ultimi 20 report
        reports = db_manager.query('''
            SELECT id, report_type, period, generated_at, sent_successfully
            FROM business_reports
            ORDER BY generated_at DESC
            LIMIT 20
        ''')
        
        # Statistiche report
        stats = db_manager.query('''
            SELECT 
                COUNT(*) as total_reports,
                SUM(CASE WHEN report_type = 'weekly' THEN 1 ELSE 0 END) as weekly_count,
                SUM(CASE WHEN report_type = 'monthly' THEN 1 ELSE 0 END) as monthly_count,
                SUM(CASE WHEN sent_successfully THEN 1 ELSE 0 END) as sent_count
            FROM business_reports
        ''', one=True)
        
        return render_template('admin_reports_dashboard.html',
                             user=session,
                             reports=reports,
                             stats=stats)
    except Exception as e:
        return f"Errore: {str(e)}", 500

@admin_reports_bp.route('/view/<int:report_id>')
def view_report(report_id):
    """Visualizza report specifico"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return redirect('/login')
    
    try:
        report = db_manager.query('''
            SELECT * FROM business_reports WHERE id = %s
        ''', (report_id,), one=True)
        
        if not report:
            return "Report non trovato", 404
        
        # Parse JSON data
        report_data = json.loads(report['data'])
        
        return render_template('report_email_template.html', report=report_data)
    except Exception as e:
        return f"Errore: {str(e)}", 500

@admin_reports_bp.route('/test/weekly')
def test_weekly():
    """Test manuale report settimanale"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return redirect('/login')
    
    try:
        report_scheduler.test_weekly_report()
        return jsonify({
            'success': True,
            'message': 'Report settimanale generato! Controlla la cartella reports/ o il database.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_reports_bp.route('/test/monthly')
def test_monthly():
    """Test manuale report mensile"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return redirect('/login')
    
    try:
        report_scheduler.test_monthly_report()
        return jsonify({
            'success': True,
            'message': 'Report mensile generato! Controlla la cartella reports/ o il database.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_reports_bp.route('/api/generate-now', methods=['POST'])
def generate_now():
    """Genera report immediatamente (API)"""
    if 'user_id' not in session or session.get('ruolo') != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 401
    
    try:
        from flask import request
        report_type = request.json.get('type', 'weekly')
        
        if report_type == 'weekly':
            report_data = report_generator.generate_weekly_report()
        else:
            report_data = report_generator.generate_monthly_report()
        
        # Salva nel database
        report_generator.save_report(report_data, session.get('email', 'admin@skaila.app'))
        
        return jsonify({
            'success': True,
            'report': report_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
