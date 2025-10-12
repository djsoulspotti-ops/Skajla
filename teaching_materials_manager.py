"""
SKAILA Teaching Materials Manager
Sistema upload e gestione materiali didattici per professori
"""

import os
from typing import Dict, List, Optional, BinaryIO
from datetime import datetime
from werkzeug.utils import secure_filename
from database_manager import db_manager

class TeachingMaterialsManager:
    """Gestione materiali didattici"""
    
    UPLOAD_FOLDER = 'uploads/teaching_materials'
    ALLOWED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'mp4': 'video/mp4',
        'mp3': 'audio/mpeg',
        'zip': 'application/zip'
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    def __init__(self):
        """Inizializza manager"""
        self._ensure_upload_folder()
    
    def _ensure_upload_folder(self):
        """Crea cartella upload se non esiste"""
        if not os.path.exists(self.UPLOAD_FOLDER):
            os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
            print(f"📁 Created upload folder: {self.UPLOAD_FOLDER}")
    
    def allowed_file(self, filename: str) -> bool:
        """Verifica se file è permesso"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def get_file_type(self, filename: str) -> str:
        """Ottieni tipo file"""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return self.ALLOWED_EXTENSIONS.get(ext, 'unknown')
    
    def upload_material(self, teacher_id: int, file, title: str, description: str,
                       subject: str, classe: Optional[str] = None, is_public: bool = False) -> Dict:
        """Upload materiale didattico"""
        
        # Validate teacher
        teacher = db_manager.query('SELECT ruolo FROM utenti WHERE id = ?', (teacher_id,), one=True)
        if not teacher or teacher['ruolo'] != 'docente':
            return {'error': 'Solo i docenti possono caricare materiali'}
        
        # Validate file
        if not file or not file.filename:
            return {'error': 'Nessun file selezionato'}
        
        if not self.allowed_file(file.filename):
            return {'error': f'Tipo file non permesso. Usa: {", ".join(self.ALLOWED_EXTENSIONS.keys())}'}
        
        # Check file size (if available)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            return {'error': f'File troppo grande. Max {self.MAX_FILE_SIZE // (1024*1024)} MB'}
        
        # Generate safe filename with timestamp
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{teacher_id}_{timestamp}_{original_filename}"
        
        # Save file
        file_path = os.path.join(self.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Save to database
        cursor = db_manager.execute('''
            INSERT INTO teaching_materials 
            (teacher_id, title, description, subject, class, file_name, file_path, 
             file_type, file_size, is_public)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_id, title, description, subject, classe, original_filename, 
              file_path, self.get_file_type(original_filename), file_size, is_public))
        
        material_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0
        
        return {
            'success': True,
            'material_id': material_id,
            'filename': original_filename,
            'file_size': file_size,
            'message': 'Materiale caricato con successo!'
        }
    
    def get_materials(self, user_id: int, subject: Optional[str] = None, 
                     classe: Optional[str] = None, teacher_id: Optional[int] = None) -> List[Dict]:
        """Lista materiali disponibili"""
        
        # Get user info
        user = db_manager.query('SELECT ruolo, classe FROM utenti WHERE id = ?', (user_id,), one=True)
        
        if not user:
            return []
        
        # Build query based on role
        query = '''
            SELECT tm.*, u.nome as teacher_name, u.cognome as teacher_surname
            FROM teaching_materials tm
            JOIN utenti u ON tm.teacher_id = u.id
            WHERE 1=1
        '''
        params = []
        
        # Students can only see public or their class materials
        if user['ruolo'] == 'studente':
            query += ' AND (tm.is_public = TRUE OR tm.class = ?)'
            params.append(user['classe'])
        
        # Teachers see their own + public
        elif user['ruolo'] == 'docente':
            query += ' AND (tm.teacher_id = ? OR tm.is_public = TRUE)'
            params.append(user_id)
        
        # Filters
        if subject:
            query += ' AND tm.subject = ?'
            params.append(subject)
        
        if classe:
            query += ' AND (tm.class = ? OR tm.class IS NULL)'
            params.append(classe)
        
        if teacher_id:
            query += ' AND tm.teacher_id = ?'
            params.append(teacher_id)
        
        query += ' ORDER BY tm.upload_date DESC'
        
        materials = db_manager.query(query, tuple(params))
        
        result = []
        for mat in materials:
            result.append({
                'id': mat['id'],
                'title': mat['title'],
                'description': mat['description'],
                'subject': mat['subject'],
                'class': mat['class'],
                'teacher': f"{mat['teacher_name']} {mat['teacher_surname']}",
                'file_name': mat['file_name'],
                'file_type': mat['file_type'],
                'file_size': self._format_file_size(mat['file_size']),
                'upload_date': mat['upload_date'],
                'downloads': mat['downloads'],
                'is_public': mat['is_public']
            })
        
        return result
    
    def download_material(self, material_id: int, user_id: int) -> Dict:
        """Download materiale"""
        
        material = db_manager.query('''
            SELECT * FROM teaching_materials WHERE id = ?
        ''', (material_id,), one=True)
        
        if not material:
            return {'error': 'Materiale non trovato'}
        
        # Check permissions
        user = db_manager.query('SELECT ruolo, classe FROM utenti WHERE id = ?', (user_id,), one=True)
        
        if user['ruolo'] == 'studente':
            if not material['is_public'] and material['class'] != user['classe']:
                return {'error': 'Non hai i permessi per scaricare questo materiale'}
        
        # Update download count
        db_manager.execute('''
            UPDATE teaching_materials SET downloads = downloads + 1 WHERE id = ?
        ''', (material_id,))
        
        # Log download
        db_manager.execute('''
            INSERT INTO material_downloads (material_id, user_id) VALUES (?, ?)
        ''', (material_id, user_id))
        
        return {
            'success': True,
            'file_path': material['file_path'],
            'file_name': material['file_name'],
            'file_type': material['file_type']
        }
    
    def delete_material(self, material_id: int, user_id: int) -> Dict:
        """Elimina materiale (solo proprietario o admin)"""
        
        material = db_manager.query('''
            SELECT * FROM teaching_materials WHERE id = ?
        ''', (material_id,), one=True)
        
        if not material:
            return {'error': 'Materiale non trovato'}
        
        # Check permissions
        user = db_manager.query('SELECT ruolo FROM utenti WHERE id = ?', (user_id,), one=True)
        
        if material['teacher_id'] != user_id and user['ruolo'] != 'admin':
            return {'error': 'Solo il proprietario o admin può eliminare'}
        
        # Delete file from disk
        if os.path.exists(material['file_path']):
            os.remove(material['file_path'])
        
        # Delete from database
        db_manager.execute('DELETE FROM teaching_materials WHERE id = ?', (material_id,))
        db_manager.execute('DELETE FROM material_downloads WHERE material_id = ?', (material_id,))
        
        return {'success': True, 'message': 'Materiale eliminato'}
    
    def get_teacher_statistics(self, teacher_id: int) -> Dict:
        """Statistiche materiali docente"""
        
        stats = db_manager.query('''
            SELECT 
                COUNT(*) as total_materials,
                SUM(downloads) as total_downloads,
                SUM(file_size) as total_size
            FROM teaching_materials WHERE teacher_id = ?
        ''', (teacher_id,), one=True)
        
        # Most downloaded
        most_downloaded = db_manager.query('''
            SELECT title, downloads FROM teaching_materials
            WHERE teacher_id = ?
            ORDER BY downloads DESC LIMIT 5
        ''', (teacher_id,))
        
        # By subject
        by_subject = db_manager.query('''
            SELECT subject, COUNT(*) as count, SUM(downloads) as downloads
            FROM teaching_materials
            WHERE teacher_id = ?
            GROUP BY subject
            ORDER BY count DESC
        ''', (teacher_id,))
        
        return {
            'total_materials': stats['total_materials'] if stats else 0,
            'total_downloads': stats['total_downloads'] if stats else 0,
            'total_size': self._format_file_size(stats['total_size']) if stats and stats['total_size'] else '0 B',
            'most_downloaded': [{'title': m['title'], 'downloads': m['downloads']} for m in most_downloaded],
            'by_subject': [{'subject': s['subject'], 'count': s['count'], 'downloads': s['downloads']} for s in by_subject]
        }
    
    def search_materials(self, user_id: int, query: str) -> List[Dict]:
        """Cerca materiali"""
        
        user = db_manager.query('SELECT ruolo, classe FROM utenti WHERE id = ?', (user_id,), one=True)
        
        search_query = '''
            SELECT tm.*, u.nome as teacher_name, u.cognome as teacher_surname
            FROM teaching_materials tm
            JOIN utenti u ON tm.teacher_id = u.id
            WHERE (tm.title LIKE ? OR tm.description LIKE ? OR tm.subject LIKE ?)
        '''
        params = [f'%{query}%', f'%{query}%', f'%{query}%']
        
        if user['ruolo'] == 'studente':
            search_query += ' AND (tm.is_public = TRUE OR tm.class = ?)'
            params.append(user['classe'])
        elif user['ruolo'] == 'docente':
            search_query += ' AND (tm.teacher_id = ? OR tm.is_public = TRUE)'
            params.append(user_id)
        
        search_query += ' ORDER BY tm.upload_date DESC LIMIT 20'
        
        results = db_manager.query(search_query, tuple(params))
        
        return [
            {
                'id': r['id'],
                'title': r['title'],
                'description': r['description'],
                'subject': r['subject'],
                'teacher': f"{r['teacher_name']} {r['teacher_surname']}",
                'file_name': r['file_name']
            }
            for r in results
        ]
    
    def _format_file_size(self, size: int) -> str:
        """Formatta dimensione file"""
        if not size:
            return '0 B'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# Initialize
materials_manager = TeachingMaterialsManager()
print("✅ Teaching Materials Manager inizializzato!")
