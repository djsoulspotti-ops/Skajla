"""
SKAILA - Email Sender
Sistema per invio email report (tramite integrazione Resend)
"""

import os
from datetime import datetime
from shared.error_handling import get_logger

logger = get_logger(__name__)

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
            logger.warning(
                event_type='resend_not_configured',
                domain='email',
                recipient_email=recipient_email,
                report_type=report_data.get('type'),
                message='Resend API not configured, falling back to file save'
            )
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
                logger.info(
                    event_type='email_sent_success',
                    domain='email',
                    recipient_email=recipient_email,
                    report_type=report_data.get('type'),
                    report_period=report_data.get('period'),
                    message='Email report sent successfully'
                )
                return True
            else:
                logger.error(
                    event_type='email_send_failed',
                    domain='email',
                    recipient_email=recipient_email,
                    report_type=report_data.get('type'),
                    status_code=response.status_code,
                    response_text=response.text,
                    message='Failed to send email via Resend API'
                )
                return False
                
        except Exception as e:
            logger.error(
                event_type='email_send_exception',
                domain='email',
                recipient_email=recipient_email,
                report_type=report_data.get('type'),
                error=str(e),
                error_type=type(e).__name__,
                message='Exception during email send, falling back to file save',
                exc_info=True
            )
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
            
            logger.info(
                event_type='report_saved_to_file',
                domain='email',
                recipient_email=recipient_email,
                report_type=report_data.get('type'),
                filename=filename,
                message='Report saved to file (Resend not configured)'
            )
            return True
        except Exception as e:
            logger.error(
                event_type='file_save_failed',
                domain='email',
                recipient_email=recipient_email,
                report_type=report_data.get('type'),
                error=str(e),
                error_type=type(e).__name__,
                message='Failed to save report to file',
                exc_info=True
            )
            return False

# Istanza globale
email_sender = EmailSender()
