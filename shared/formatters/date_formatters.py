"""
SKAILA - Formattatori Date Centralizzati
Formattazione consistente di date e tempi in tutta l'applicazione
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union
from shared.error_handling import get_logger

logger = get_logger(__name__)

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
            except Exception as e:
                logger.warning(
                    event_type='date_parse_failed',
                    message='Failed to parse ISO date string',
                    domain='formatting',
                    format_type='format_date',
                    input_data=dt,
                    error=str(e)
                )
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
            except Exception as e:
                logger.warning(
                    event_type='datetime_parse_failed',
                    message='Failed to parse ISO datetime string',
                    domain='formatting',
                    format_type='format_datetime',
                    input_data=dt,
                    error=str(e)
                )
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
            except Exception as e:
                logger.warning(
                    event_type='time_parse_failed',
                    message='Failed to parse ISO time string',
                    domain='formatting',
                    format_type='format_time',
                    input_data=dt,
                    error=str(e)
                )
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
            except Exception as e:
                logger.warning(
                    event_type='relative_date_parse_failed',
                    message='Failed to parse ISO date for relative formatting',
                    domain='formatting',
                    format_type='format_relative',
                    input_data=dt,
                    error=str(e)
                )
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
        except Exception as e:
            logger.warning(
                event_type='date_strptime_failed',
                message='Failed to parse date with specified format',
                domain='formatting',
                format_type='parse_date',
                input_data=date_str,
                expected_format=format,
                error=str(e)
            )
            try:
                return datetime.fromisoformat(date_str).date()
            except Exception as e2:
                logger.warning(
                    event_type='date_iso_parse_failed',
                    message='Failed to parse date as ISO format',
                    domain='formatting',
                    format_type='parse_date',
                    input_data=date_str,
                    error=str(e2)
                )
                return None
    
    @staticmethod
    def parse_datetime(datetime_str: str) -> Optional[datetime]:
        """Parse stringa in oggetto datetime"""
        if not datetime_str:
            return None
        
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(
                event_type='datetime_iso_parse_failed',
                message='Failed to parse datetime as ISO format',
                domain='formatting',
                format_type='parse_datetime',
                input_data=datetime_str,
                error=str(e)
            )
            try:
                return datetime.strptime(datetime_str, DateFormatter.FORMAT_ISO_DATETIME)
            except Exception as e2:
                logger.warning(
                    event_type='datetime_strptime_failed',
                    message='Failed to parse datetime with ISO datetime format',
                    domain='formatting',
                    format_type='parse_datetime',
                    input_data=datetime_str,
                    expected_format=DateFormatter.FORMAT_ISO_DATETIME,
                    error=str(e2)
                )
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
