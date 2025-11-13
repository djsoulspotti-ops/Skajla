"""
SKAILA - Formattatori File Centralizzati
Formattazione consistente di file size e nomi in tutta l'applicazione
"""

from typing import Optional
import os
from shared.error_handling.structured_logger import get_logger

logger = get_logger(__name__)

class FileFormatter:
    """Formattatore centralizzato per file"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formatta dimensione file in formato leggibile"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Ottiene estensione file"""
        if not filename or '.' not in filename:
            return ""
        return filename.rsplit('.', 1)[1].lower()
    
    @staticmethod
    def get_file_icon(filename: str) -> str:
        """Ottiene icona emoji per tipo file"""
        ext = FileFormatter.get_file_extension(filename)
        
        icon_map = {
            'pdf': '📄',
            'doc': '📝',
            'docx': '📝',
            'txt': '📃',
            'ppt': '📊',
            'pptx': '📊',
            'xls': '📈',
            'xlsx': '📈',
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'png': '🖼️',
            'gif': '🖼️',
            'svg': '🖼️',
            'mp4': '🎥',
            'avi': '🎥',
            'mov': '🎥',
            'wmv': '🎥',
            'mp3': '🎵',
            'wav': '🎵',
            'zip': '📦',
            'rar': '📦',
            '7z': '📦'
        }
        
        return icon_map.get(ext, '📁')
    
    @staticmethod
    def is_safe_path(filename: str, base_dir: str) -> bool:
        """Verifica che il path non esca dalla directory base (path traversal protection)"""
        try:
            base = os.path.abspath(base_dir)
            target = os.path.abspath(os.path.join(base_dir, filename))
            return target.startswith(base)
        except Exception as e:
            logger.warning(
                event_type='path_safety_check_failed',
                domain='security',
                message='Failed to verify path safety',
                filename=filename,
                base_dir=base_dir,
                error=str(e)
            )
            return False
    
    @staticmethod
    def truncate_filename(filename: str, max_length: int = 50) -> str:
        """Tronca nome file mantenendo l'estensione"""
        if len(filename) <= max_length:
            return filename
        
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            available = max_length - len(ext) - 4
            if available > 0:
                return f"{name[:available]}...{ext}"
        
        return filename[:max_length - 3] + "..."

file_formatter = FileFormatter()
