"""
SKAILA - Report Scheduler
Sistema automatico per invio report settimanali e mensili
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os
from report_generator import report_generator
from email_sender import email_sender
from flask import render_template_string

class ReportScheduler:
    """Scheduler per report automatici"""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.recipient_email = os.getenv('ADMIN_EMAIL', 'admin@skaila.app')
        self.enabled = True
        self.app = app
    
    def start(self):
        """Avvia scheduler"""
        if not self.enabled:
            print("⚠️ Report scheduler disabilitato")
            return
        
        # Report settimanale: ogni venerdì alle 18:00
        self.scheduler.add_job(
            self.send_weekly_report,
            CronTrigger(day_of_week='fri', hour=18, minute=0),
            id='weekly_report',
            name='Report Settimanale',
            replace_existing=True
        )
        
        # Report mensile: ultimo giorno del mese alle 18:00
        self.scheduler.add_job(
            self.send_monthly_report,
            CronTrigger(day='last', hour=18, minute=0),
            id='monthly_report',
            name='Report Mensile',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("✅ Report Scheduler avviato")
        print(f"   📧 Email destinatario: {self.recipient_email}")
        print(f"   📅 Report settimanale: Ogni venerdì alle 18:00")
        print(f"   📅 Report mensile: Ultimo giorno del mese alle 18:00")
    
    def send_weekly_report(self):
        """Genera e invia report settimanale"""
        try:
            print(f"\n{'='*60}")
            print(f"📊 Generazione Report Settimanale - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            print(f"{'='*60}")
            
            # Genera report
            report_data = report_generator.generate_weekly_report()
            
            # Renderizza HTML
            html_content = self._render_report_html(report_data)
            
            # Salva nel database
            report_generator.save_report(report_data, self.recipient_email)
            
            # Invia email
            email_sender.send_report_email(
                self.recipient_email,
                report_data,
                html_content
            )
            
            print(f"✅ Report settimanale generato e inviato con successo")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Errore send_weekly_report: {e}")
    
    def send_monthly_report(self):
        """Genera e invia report mensile"""
        try:
            print(f"\n{'='*60}")
            print(f"📈 Generazione Report Mensile - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            print(f"{'='*60}")
            
            # Genera report
            report_data = report_generator.generate_monthly_report()
            
            # Renderizza HTML
            html_content = self._render_report_html(report_data)
            
            # Salva nel database
            report_generator.save_report(report_data, self.recipient_email)
            
            # Invia email
            email_sender.send_report_email(
                self.recipient_email,
                report_data,
                html_content
            )
            
            print(f"✅ Report mensile generato e inviato con successo")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Errore send_monthly_report: {e}")
    
    def _render_report_html(self, report_data):
        """Renderizza template HTML del report"""
        try:
            if not self.app:
                raise Exception("Flask app non configurata nel scheduler")
            
            with self.app.app_context():
                with open('templates/report_email_template.html', 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                html = render_template_string(template_content, report=report_data)
                return html
        except Exception as e:
            print(f"❌ Errore _render_report_html: {e}")
            return f"<html><body><h1>Errore rendering template</h1><pre>{str(e)}</pre></body></html>"
    
    def stop(self):
        """Ferma scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("🛑 Report Scheduler fermato")
    
    def test_weekly_report(self):
        """Test manuale report settimanale"""
        print("\n🧪 TEST REPORT SETTIMANALE")
        self.send_weekly_report()
    
    def test_monthly_report(self):
        """Test manuale report mensile"""
        print("\n🧪 TEST REPORT MENSILE")
        self.send_monthly_report()

# Istanza globale
report_scheduler = ReportScheduler()
