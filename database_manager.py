
import os
import sqlite3
import psycopg2
import psycopg2.pool
import eventlet
from eventlet import Queue
import time
from contextlib import contextmanager

class DatabaseManager:
    """Gestione database scalabile con supporto PostgreSQL e SQLite"""
    
    def __init__(self):
        self.db_type = 'postgresql' if os.getenv('DATABASE_URL') else 'sqlite'
        self.pool = None
        self.sqlite_pool = None
        
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
                    
        # Usa connection pooler per performance
        pooled_url = database_url.replace('.us-east-2', '-pooler.us-east-2')
        
        # Combina endpoint SNI con altre opzioni PostgreSQL
        combined_options = '-c statement_timeout=30000 -c client_encoding=UTF8'
        if endpoint_id:
            combined_options = f'endpoint={endpoint_id} {combined_options}'
        
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=pooled_url,
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
        """Context manager per gestione automatica connessioni"""
        if self.db_type == 'postgresql':
            conn = self.pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                self.pool.putconn(conn)
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
