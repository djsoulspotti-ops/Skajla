
import os
import sqlite3
import psycopg2
import psycopg2.pool
import eventlet
from eventlet import Queue
import time
from contextlib import contextmanager
from typing import Optional, Union, Any, List, Dict, Tuple

class CursorProxy:
    """Wrapper per simulare cursor.lastrowid in PostgreSQL"""
    def __init__(self, lastrowid: Optional[int] = None, rowcount: int = 0):
        self.lastrowid: Optional[int] = lastrowid
        self.rowcount: int = rowcount
    
    def __bool__(self) -> bool:
        """Truthy solo se rowcount > 0 (per compatibilità ON CONFLICT)"""
        return self.rowcount > 0

class DatabaseManager:
    """Gestione database scalabile con supporto PostgreSQL e SQLite"""
    
    def __init__(self):
        self.db_type: str = 'postgresql' if os.getenv('DATABASE_URL') else 'sqlite'
        self.pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self.sqlite_pool: Optional[Any] = None
        
        try:
            if self.db_type == 'postgresql':
                self.setup_postgresql_pool()
            else:
                self.setup_sqlite_pool()
        except Exception as e:
            print(f"Database connection failed: {e}")
            print("Falling back to SQLite...")
            self.db_type = 'sqlite'
            self.setup_sqlite_pool()
    
    def setup_postgresql_pool(self):
        """Configura connection pool PostgreSQL per alta concorrenza"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        # CRITICO: Fix PostgreSQL per Neon SNI - metodo combinato corretto
        endpoint_id = None
        if 'neon.tech' in database_url:
            # Estrai endpoint dal nome dominio (es: ep-noisy-salad-ae8vg6i0)
            import re
            match = re.search(r'ep-[^@.]+', database_url)
            if match:
                endpoint_id = match.group(0)
                print(f"⚙️ PostgreSQL: Found endpoint {endpoint_id}")
                
                # Rimuovi options esistenti dall'URL per evitare conflitti
                if '?' in database_url:
                    database_url = database_url.split('?')[0]
                    
        # Use the original DATABASE_URL directly for better compatibility
        connection_url = database_url
        
        # Combina endpoint SNI con altre opzioni PostgreSQL
        combined_options = '-c statement_timeout=30000 -c client_encoding=UTF8'
        if endpoint_id:
            combined_options = f'endpoint={endpoint_id} {combined_options}'
        
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=connection_url,
                # CRITICO: Parametri SNI richiesti da Neon per produzione
                sslmode='require',
                connect_timeout=10,
                application_name='SKAILA_Production',
                # Ottimizzazioni combinate con endpoint SNI
                options=combined_options
            )
            print("✅ PostgreSQL pool Neon SNI configurato per produzione")
        except Exception as e:
            print(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    
    def setup_sqlite_pool(self):
        """Connection pool SQLite ottimizzato"""
        class SQLitePool:
            def __init__(self, max_connections=10):
                self.max_connections = max_connections
                self.pool = Queue(maxsize=max_connections)
                self.lock = eventlet.semaphore.Semaphore(1)
                
                # Pre-crea connessioni ottimizzate
                for _ in range(max_connections):
                    conn = sqlite3.connect('skaila.db', 
                                         timeout=30.0, 
                                         check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    # Ottimizzazioni SQLite per alta concorrenza
                    conn.execute('PRAGMA journal_mode=WAL')
                    conn.execute('PRAGMA synchronous=NORMAL') 
                    conn.execute('PRAGMA cache_size=50000')
                    conn.execute('PRAGMA temp_store=memory')
                    conn.execute('PRAGMA busy_timeout=30000')
                    conn.execute('PRAGMA wal_autocheckpoint=1000')
                    self.pool.put(conn)
            
            def getconn(self):
                try:
                    # Use eventlet-compatible non-blocking get
                    return self.pool.get(block=True, timeout=5)
                except:
                    # Crea connessione temporanea se pool esaurito
                    return self._create_connection()
            
            def putconn(self, conn):
                try:
                    # Use eventlet-compatible non-blocking put
                    self.pool.put(conn, block=True, timeout=1)
                except:
                    conn.close()
            
            def _create_connection(self):
                conn = sqlite3.connect('skaila.db', timeout=30.0, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                return conn
        
        self.sqlite_pool = SQLitePool()
        print("✅ SQLite pool ottimizzato configurato")
    
    @contextmanager
    def get_connection(self):
        """Context manager per gestione automatica connessioni con retry atomico per Neon sleep"""
        if self.db_type == 'postgresql':
            max_retries = 8  # Più tentativi per gestire Neon sleep
            retry_count = 0
            conn = None
            last_error = None
            
            while retry_count < max_retries:
                conn = None
                try:
                    # Ottieni connessione dal pool
                    conn = self.pool.getconn()
                    
                    # TEST ATOMICO: Verifica connessione subito prima dell'uso
                    # Questo garantisce che sia valida nel momento esatto della query
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                    cursor.close()
                    
                    # Connessione verificata - procedi con operazione utente
                    yield conn
                    conn.commit()
                    
                    # Restituisci connessione al pool
                    self.pool.putconn(conn)
                    return  # Success
                    
                except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                    retry_count += 1
                    last_error = e
                    error_msg = str(e).lower()
                    
                    print(f"⚠️ Database error (attempt {retry_count}/{max_retries}): {error_msg[:100]}")
                    
                    # IMPORTANTE: Chiudi connessione fallita
                    if conn:
                        try:
                            self.pool.putconn(conn, close=True)
                        except:
                            pass
                        conn = None
                    
                    # Ricrea pool SOLO se errore di connessione/SSL
                    if any(keyword in error_msg for keyword in ['ssl', 'connection', 'closed', 'eof', 'timeout']):
                        print("🔄 Neon sleep rilevato - ricreazione pool...")
                        try:
                            self.pool.closeall()
                        except:
                            pass
                        
                        self.setup_postgresql_pool()
                        
                        # Attendi wake-up Neon (2s fissi per primo tentativo, poi progressivo)
                        import time
                        if retry_count == 1:
                            time.sleep(2)  # Primo tentativo: attendi wake-up
                        else:
                            wait_time = min(retry_count * 0.3, 2)  # Max 2 secondi
                            time.sleep(wait_time)
                    else:
                        # Errore non di connessione - attendi breve
                        import time
                        time.sleep(0.5)
                    
                    # Ultimo tentativo fallito
                    if retry_count >= max_retries:
                        print(f"❌ Database connection failed definitivamente")
                        raise last_error if last_error else Exception("Database unavailable")
                    
                except Exception as e:
                    if conn:
                        try:
                            conn.rollback()
                            self.pool.putconn(conn)
                        except:
                            pass
                    raise e
        else:
            conn = self.sqlite_pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                self.sqlite_pool.putconn(conn)
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Esegue query con gestione automatica connessioni"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.lastrowid if cursor.lastrowid else True
    
    def execute_many(self, query, params_list):
        """Esegue query batch per migliori performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def _adapt_params(self, query, params):
        """Adatta parametri per compatibilità PostgreSQL/SQLite"""
        if not params:
            return query, params
            
        if self.db_type == 'postgresql':
            # Converti ? in %s per PostgreSQL
            adapted_query = query.replace('?', '%s')
            return adapted_query, params
        else:
            # SQLite usa ? - nessuna modifica necessaria
            return query, params
    
    def query(self, sql: str, params: Optional[Tuple] = None, one: bool = False, many: bool = True) -> Union[Optional[Dict[str, Any]], List[Dict[str, Any]], List[Any]]:
        """Wrapper unificato per SELECT con risultati dict-like"""
        adapted_sql, adapted_params = self._adapt_params(sql, params)
        
        with self.get_connection() as conn:
            if self.db_type == 'postgresql':
                # Usa DictCursor per PostgreSQL
                from psycopg2.extras import DictCursor
                cursor = conn.cursor(cursor_factory=DictCursor)
            else:
                # SQLite ha già Row factory configurata
                cursor = conn.cursor()
            
            cursor.execute(adapted_sql, adapted_params or ())
            
            if one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif many:
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []
            else:
                return cursor.fetchall()
    
    def execute(self, sql: str, params: Optional[Tuple] = None) -> Union[CursorProxy, int, Any]:
        """Wrapper unificato per INSERT/UPDATE/DELETE con supporto RETURNING id intelligente"""
        adapted_sql, adapted_params = self._adapt_params(sql, params)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # PostgreSQL: Aggiungi RETURNING id SOLO se sicuro
            returning_added = False
            if self.db_type == 'postgresql':
                if adapted_sql.strip().upper().startswith('INSERT'):
                    # Aggiungi RETURNING id SOLO se:
                    # 1. Non ha già RETURNING
                    # 2. Non ha ON CONFLICT (potrebb not inserire)
                    if ('RETURNING' not in adapted_sql.upper() and 
                        'ON CONFLICT' not in adapted_sql.upper()):
                        # Rimuovi eventuale punto e virgola finale
                        clean_sql = adapted_sql.rstrip().rstrip(';')
                        adapted_sql = f"{clean_sql} RETURNING id"
                        returning_added = True
            
            cursor.execute(adapted_sql, adapted_params or ())
            
            # Restituisce CursorProxy per compatibilità con lastrowid
            if self.db_type == 'postgresql':
                if adapted_sql.strip().upper().startswith('INSERT'):
                    # Se abbiamo aggiunto RETURNING, fetch il risultato
                    if returning_added or 'RETURNING' in adapted_sql.upper():
                        try:
                            result = cursor.fetchone()
                            if result:
                                inserted_id = result[0] if isinstance(result, tuple) else result
                                return CursorProxy(lastrowid=inserted_id, rowcount=1)
                        except Exception as e:
                            # Tabella senza colonna id - fallback sicuro
                            pass
                    
                    # Fallback: usa rowcount (per ON CONFLICT o tabelle senza id)
                    return CursorProxy(lastrowid=0, rowcount=cursor.rowcount)
                    
                # UPDATE/DELETE - ritorna rowcount
                return cursor.rowcount
            else:
                # SQLite - ritorna cursor originale per compatibilità
                return cursor
    
    def create_optimized_indexes(self):
        """Crea indici per performance ottimali"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_utenti_email ON utenti(email)",
            "CREATE INDEX IF NOT EXISTS idx_utenti_status_classe ON utenti(status_online, classe)",
            "CREATE INDEX IF NOT EXISTS idx_messaggi_chat_timestamp ON messaggi(chat_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_partecipanti_user_chat ON partecipanti_chat(utente_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_subject ON ai_conversations(utente_id, subject_detected)"
            # FIXME: user_gamification table non esiste ancora - commentato per evitare errori
            # "CREATE INDEX IF NOT EXISTS idx_gamification_user_timestamp ON user_gamification(user_id, last_updated)"
        ]
        
        for index_sql in indexes:
            try:
                self.execute_query(index_sql)
            except Exception as e:
                print(f"⚠️ Indice già esistente: {e}")
        
        print("✅ Indici database ottimizzati")

# Istanza globale
db_manager = DatabaseManager()
