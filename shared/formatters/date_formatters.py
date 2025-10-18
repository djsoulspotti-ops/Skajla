"""
SKAILA - Formattatori Date Centralizzati
Formattazione consistente di date e tempi in tutta l'applicazione
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union

class DateFormatter:
    """Formattatore centralizzato per date"""
    
    FORMAT_DATE = '%d/%m/%Y'
    FORMAT_DATETIME = '%d/%m/%Y %H:%M'
    FORMAT_TIME = '%H:%M'
    FORMAT_ISO = '%Y-%m-%d'
    FORMAT_ISO_DATETIME = '%Y-%m-%d %H:%M:%S'
    
    @staticmethod
    def format_date(dt: Union[datetime, date, str]) -> str:
        """Formatta data in formato italiano (DD/MM/YYYY)"""
        if not dt:
            return ""
        
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        
        if isinstance(dt, datetime):
            return dt.strftime(DateFormatter.FORMAT_DATE)
        elif isinstance(dt, date):
            return dt.strftime(DateFormatter.FORMAT_DATE)
        
        return str(dt)
    
    @staticmethod
    def format_datetime(dt: Union[datetime, str]) -> str:
        """Formatta data e ora (DD/MM/YYYY HH:MM)"""
        if not dt:
            return ""
        
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        
        if isinstance(dt, datetime):
            return dt.strftime(DateFormatter.FORMAT_DATETIME)
        
        return str(dt)
    
    @staticmethod
    def format_time(dt: Union[datetime, str]) -> str:
        """Formatta solo ora (HH:MM)"""
        if not dt:
            return ""
        
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        
        if isinstance(dt, datetime):
            return dt.strftime(DateFormatter.FORMAT_TIME)
        
        return str(dt)
    
    @staticmethod
    def format_relative(dt: Union[datetime, date, str]) -> str:
        """Formatta data relativa (es: 'oggi', '2 giorni fa')"""
        if not dt:
            return ""
        
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return str(dt)
        
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time())
        
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Adesso"
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f"{mins} minut{'o' if mins == 1 else 'i'} fa"
            elif diff.seconds < 86400:
                hours = diff.seconds // 3600
                return f"{hours} or{'a' if hours == 1 else 'e'} fa"
        elif diff.days == 1:
            return "Ieri"
        elif diff.days < 7:
            return f"{diff.days} giorni fa"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} settiman{'a' if weeks == 1 else 'e'} fa"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} mes{'e' if months == 1 else 'i'} fa"
        else:
            years = diff.days // 365
            return f"{years} ann{'o' if years == 1 else 'i'} fa"
    
    @staticmethod
    def parse_date(date_str: str, format: str = FORMAT_ISO) -> Optional[date]:
        """Parse stringa in oggetto date"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, format).date()
        except:
            try:
                return datetime.fromisoformat(date_str).date()
            except:
                return None
    
    @staticmethod
    def parse_datetime(datetime_str: str) -> Optional[datetime]:
        """Parse stringa in oggetto datetime"""
        if not datetime_str:
            return None
        
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(datetime_str, DateFormatter.FORMAT_ISO_DATETIME)
            except:
                return None
    
    @staticmethod
    def get_school_year() -> str:
        """Ottiene anno scolastico corrente (es: 2024/2025)"""
        today = date.today()
        if today.month >= 9:
            return f"{today.year}/{today.year + 1}"
        else:
            return f"{today.year - 1}/{today.year}"
    
    @staticmethod
    def is_weekend(dt: Union[datetime, date]) -> bool:
        """Verifica se una data è weekend"""
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.weekday() >= 5
    
    @staticmethod
    def get_week_number(dt: Union[datetime, date]) -> int:
        """Ottiene numero settimana dell'anno"""
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.isocalendar()[1]

date_formatter = DateFormatter()
