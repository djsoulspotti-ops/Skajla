from services.database.database_manager import db_manager
from shared.error_handling import (
    handle_errors,
    DatabaseError,
    ValidationError,
    get_logger
)
from datetime import datetime
import json

logger = get_logger(__name__)

class CalendarSystem:
    """Sistema calendario intelligente con storage flessibile JSON"""
    
    def __init__(self):
        self.init_calendar_tables()
    
    @handle_errors
    def init_calendar_tables(self):
        """Inizializza tabelle calendario con supporto JSONB per flessibilità"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            is_postgres = db_manager.db_type == 'postgresql'
            serial_type = 'SERIAL PRIMARY KEY' if is_postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'
            timestamp_type = 'TIMESTAMP' if is_postgres else 'DATETIME'
            json_type = 'JSONB' if is_postgres else 'TEXT'
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS schedules (
                    id {serial_type},
                    user_id INTEGER NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL CHECK (event_type IN ('lesson', 'homework', 'exam', 'event', 'school_event', 'meeting', 'other')),
                    title TEXT NOT NULL,
                    start_datetime {timestamp_type} NOT NULL,
                    end_datetime {timestamp_type},
                    all_day BOOLEAN DEFAULT FALSE,
                    recurrence TEXT CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly')),
                    event_data {json_type},
                    created_by INTEGER NOT NULL REFERENCES utenti(id),
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_schedules_user_date 
                ON schedules(user_id, start_datetime DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_schedules_type 
                ON schedules(event_type, start_datetime)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_schedules_active 
                ON schedules(is_active, start_datetime)
            ''')
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS school_wide_events (
                    id {serial_type},
                    scuola_id INTEGER NOT NULL REFERENCES scuole(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_datetime {timestamp_type} NOT NULL,
                    end_datetime {timestamp_type},
                    all_day BOOLEAN DEFAULT TRUE,
                    created_by INTEGER NOT NULL REFERENCES utenti(id),
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_school_events_school_date 
                ON school_wide_events(scuola_id, start_datetime DESC)
            ''')
            
            conn.commit()
            
            logger.info(
                event_type='calendar_tables_initialized',
                domain='calendar',
                message='Tabelle calendario create con successo (JSONB storage per flessibilità)'
            )
    
    @handle_errors
    def create_event(self, user_id: int, event_type: str, title: str, 
                     start_datetime: str, end_datetime: str = None, 
                     event_data: dict = None, all_day: bool = False,
                     recurrence: str = 'none') -> dict:
        """
        Crea un nuovo evento calendario
        
        event_data può contenere:
        - subject: "Matematica"
        - class_name: "5A"
        - class_id: 123
        - room: "Aula 201"
        - description: "Verifica di algebra"
        - homework: "Esercizi pag. 45"
        - attachments: [...]
        """
        if event_data is None:
            event_data = {}
        
        event_data_json = json.dumps(event_data) if db_manager.db_type == 'sqlite' else event_data
        
        result = db_manager.execute(
            '''
            INSERT INTO schedules 
            (user_id, event_type, title, start_datetime, end_datetime, all_day, recurrence, event_data, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            ''',
            (user_id, event_type, title, start_datetime, end_datetime, all_day, recurrence, event_data_json, user_id)
        )
        
        logger.info(
            event_type='calendar_event_created',
            domain='calendar',
            user_id=user_id,
            event_id=result[0]['id'],
            event_type_name=event_type,
            title=title
        )
        
        return {
            'id': result[0]['id'],
            'created_at': str(result[0]['created_at'])
        }
    
    @handle_errors
    def get_user_events(self, user_id: int, start_date: str = None, end_date: str = None) -> list:
        """Ottieni eventi per un utente in un range di date"""
        query = '''
            SELECT id, event_type, title, start_datetime, end_datetime, 
                   all_day, recurrence, event_data, created_at
            FROM schedules
            WHERE user_id = %s AND is_active = TRUE
        '''
        params = [user_id]
        
        if start_date:
            query += ' AND start_datetime >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND start_datetime <= %s'
            params.append(end_date)
        
        query += ' ORDER BY start_datetime ASC'
        
        events = db_manager.execute(query, tuple(params))
        
        for event in events:
            if db_manager.db_type == 'sqlite' and event.get('event_data'):
                try:
                    event['event_data'] = json.loads(event['event_data'])
                except:
                    event['event_data'] = {}
        
        return events
    
    @handle_errors
    def get_class_schedule(self, class_id: int, start_date: str = None, end_date: str = None) -> list:
        """Ottieni tutti gli eventi per una classe specifica"""
        query = '''
            SELECT s.id, s.event_type, s.title, s.start_datetime, s.end_datetime,
                   s.all_day, s.event_data, s.created_by,
                   u.nome, u.cognome, u.ruolo
            FROM schedules s
            JOIN utenti u ON s.created_by = u.id
            WHERE s.is_active = TRUE
        '''
        params = []
        
        if db_manager.db_type == 'postgresql':
            query += " AND s.event_data->>'class_id' = %s"
        else:
            query += " AND json_extract(s.event_data, '$.class_id') = %s"
        
        params.append(str(class_id))
        
        if start_date:
            query += ' AND s.start_datetime >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND s.start_datetime <= %s'
            params.append(end_date)
        
        query += ' ORDER BY s.start_datetime ASC'
        
        events = db_manager.execute(query, tuple(params))
        
        for event in events:
            if db_manager.db_type == 'sqlite' and event.get('event_data'):
                try:
                    event['event_data'] = json.loads(event['event_data'])
                except:
                    event['event_data'] = {}
        
        return events
    
    @handle_errors
    def update_event(self, event_id: int, user_id: int, updates: dict) -> bool:
        """Aggiorna un evento (solo il creatore può modificare)"""
        from shared.error_handling import AuthError
        
        ownership_check = db_manager.execute(
            'SELECT created_by FROM schedules WHERE id = %s AND is_active = TRUE',
            (event_id,)
        )
        
        if not ownership_check:
            raise ValidationError("Evento non trovato")
        
        if ownership_check[0]['created_by'] != user_id:
            raise AuthError("Non puoi modificare eventi creati da altri utenti")
        
        allowed_fields = ['title', 'start_datetime', 'end_datetime', 'all_day', 'event_type', 'event_data', 'recurrence']
        
        set_clauses = []
        params = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'event_data':
                    value = json.dumps(value) if db_manager.db_type == 'sqlite' else value
                set_clauses.append(f'{field} = %s')
                params.append(value)
        
        if not set_clauses:
            raise ValidationError("Nessun campo valido da aggiornare")
        
        set_clauses.append('updated_at = CURRENT_TIMESTAMP')
        params.extend([event_id, user_id])
        
        query = f'''
            UPDATE schedules 
            SET {', '.join(set_clauses)}
            WHERE id = %s AND created_by = %s
        '''
        
        db_manager.execute(query, tuple(params))
        
        logger.info(
            event_type='calendar_event_updated',
            domain='calendar',
            event_id=event_id,
            user_id=user_id,
            fields_updated=list(updates.keys())
        )
        
        return True
    
    @handle_errors
    def delete_event(self, event_id: int, user_id: int) -> bool:
        """Soft delete di un evento (solo il creatore può eliminare)"""
        from shared.error_handling import AuthError
        
        ownership_check = db_manager.execute(
            'SELECT created_by FROM schedules WHERE id = %s AND is_active = TRUE',
            (event_id,)
        )
        
        if not ownership_check:
            raise ValidationError("Evento non trovato")
        
        if ownership_check[0]['created_by'] != user_id:
            raise AuthError("Non puoi eliminare eventi creati da altri utenti")
        
        db_manager.execute(
            'UPDATE schedules SET is_active = FALSE WHERE id = %s AND created_by = %s',
            (event_id, user_id)
        )
        
        logger.info(
            event_type='calendar_event_deleted',
            domain='calendar',
            event_id=event_id,
            user_id=user_id
        )
        
        return True
    
    @handle_errors
    def create_school_wide_event(self, scuola_id: int, created_by: int, 
                                  event_type: str, title: str, description: str,
                                  start_datetime: str, end_datetime: str = None,
                                  all_day: bool = True) -> dict:
        """Crea evento visibile a tutta la scuola (solo dirigente)"""
        result = db_manager.execute(
            '''
            INSERT INTO school_wide_events 
            (scuola_id, event_type, title, description, start_datetime, end_datetime, all_day, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            ''',
            (scuola_id, event_type, title, description, start_datetime, end_datetime, all_day, created_by)
        )
        
        logger.info(
            event_type='school_wide_event_created',
            domain='calendar',
            scuola_id=scuola_id,
            event_id=result[0]['id'],
            created_by=created_by,
            title=title
        )
        
        return {
            'id': result[0]['id'],
            'created_at': str(result[0]['created_at'])
        }
    
    @handle_errors
    def get_school_wide_events(self, scuola_id: int, start_date: str = None, end_date: str = None) -> list:
        """Ottieni eventi scolastici globali"""
        query = '''
            SELECT id, event_type, title, description, start_datetime, end_datetime, all_day, created_at
            FROM school_wide_events
            WHERE scuola_id = %s AND is_active = TRUE
        '''
        params = [scuola_id]
        
        if start_date:
            query += ' AND start_datetime >= %s'
            params.append(start_date)
        
        if end_date:
            query += ' AND start_datetime <= %s'
            params.append(end_date)
        
        query += ' ORDER BY start_datetime ASC'
        
        return db_manager.execute(query, tuple(params))

calendar_system = CalendarSystem()
