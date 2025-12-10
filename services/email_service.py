
"""
SKAJLA Email Service - Production Ready
Gestione invio email con SMTP reale e fallback
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from environment_manager import env_manager

class EmailService:
    """Servizio email con SMTP configurabile"""
    
    def __init__(self):
        self.smtp_server = env_manager.get_config('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(env_manager.get_config('SMTP_PORT', '587'))
        self.smtp_user = env_manager.get_config('SMTP_USERNAME', '')
        self.smtp_password = env_manager.get_config('SMTP_PASSWORD', '')
        self.from_email = env_manager.get_config('FROM_EMAIL', 'noreply@skaila.edu')
        self.mock_mode = not (self.smtp_user and self.smtp_password)
    
    def send_email(self, to: List[str], subject: str, body_html: str, 
                   body_text: Optional[str] = None) -> bool:
        """Invia email con fallback a mock"""
        
        if self.mock_mode:
            print(f"📧 [MOCK] Email a {to}: {subject}")
            return True
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to)
            
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email inviata a {to}")
            return True
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

email_service = EmailService()
