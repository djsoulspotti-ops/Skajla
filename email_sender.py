"""
SKAILA - Email Sender
Sistema per invio email report (tramite integrazione Resend)
"""

import os
from datetime import datetime

class EmailSender:
    """Gestisce invio email tramite Resend"""
    
    def __init__(self):
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('REPORT_FROM_EMAIL', 'reports@skaila.app')
        self.resend_available = self.resend_api_key is not None
    
    def send_report_email(self, recipient_email, report_data, html_content):
        """
        Invia email con report
        
        Args:
            recipient_email: Email destinatario
            report_data: Dizionario con dati report
            html_content: HTML del report
        
        Returns:
            bool: True se invio riuscito, False altrimenti
        """
        if not self.resend_available:
            print("⚠️ Resend non configurato - Report salvato solo nel database")
            return self._save_to_file(recipient_email, report_data, html_content)
        
        try:
            import requests
            
            subject = self._get_subject(report_data)
            
            response = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {self.resend_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': self.from_email,
                    'to': recipient_email,
                    'subject': subject,
                    'html': html_content
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Email report inviata a {recipient_email}")
                return True
            else:
                print(f"❌ Errore invio email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Errore send_report_email: {e}")
            return self._save_to_file(recipient_email, report_data, html_content)
    
    def _get_subject(self, report_data):
        """Genera subject email in base al tipo report"""
        if report_data['type'] == 'weekly':
            return f"📊 SKAILA Report Settimanale - {report_data['period']}"
        else:
            return f"📈 SKAILA Report Mensile - {report_data['period']}"
    
    def _save_to_file(self, recipient_email, report_data, html_content):
        """Salva report come file HTML (fallback se Resend non disponibile)"""
        try:
            filename = f"reports/report_{report_data['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            os.makedirs('reports', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"💾 Report salvato come file: {filename}")
            print(f"👉 Configurare Resend per invio automatico via email")
            return True
        except Exception as e:
            print(f"❌ Errore save_to_file: {e}")
            return False

# Istanza globale
email_sender = EmailSender()
