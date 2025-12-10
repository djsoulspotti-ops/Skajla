import os
import sqlite3
import psycopg2
import psycopg2.pool
import eventlet
from eventlet import Queue
import time
from contextlib import contextmanager
from typing import Optional, Union, Any, List, Dict, Tuple

# Error handling framework
from shared.error_handling import (
    DatabaseError,
    DatabaseTransientError,
    DatabaseConnectionError,
    DatabaseQueryError,
    get_logger
)

# Initialize structured logger for database operations
logger = get_logger(__name__)

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
            logger.error(
                event_type='postgres_connection_failed',
                domain='database',
                message=f'Database connection failed: {e}',
                error=str(e),
                exc_info=True
            )
            logger.warning(
                event_type='sqlite_fallback',
                domain='database',
                message='Falling back to SQLite due to PostgreSQL connection failure'
            )
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
                logger.debug(
                    event_type='postgres_endpoint_detected',
                    domain='database',
                    message=f'PostgreSQL: Found endpoint {endpoint_id}',
                    endpoint_id=endpoint_id
                )

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
                minconn=10,  # Minimo 10 connessioni ready
                maxconn=50,  # Max 50 connessioni per gestire più utenti
                dsn=connection_url,
                # CRITICO: Parametri SNI richiesti da Neon per produzione
                sslmode='require',
                connect_timeout=10,
                application_name='SKAJLA_Production',
                # Ottimizzazioni combinate con endpoint SNI
                options=combined_options
            )
            logger.info(
                event_type='postgres_pool_configured',
                domain='database',
                message='PostgreSQL pool Neon SNI configurato per produzione',
                min_connections=10,
                max_connections=50
            )
        except Exception as e:
            logger.error(
                event_type='postgres_pool_creation_failed',
                domain='database',
                message=f'Failed to create PostgreSQL connection pool: {e}',
                error=str(e),
                exc_info=True
            )
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
                """Get connection from pool with fallback to temp connection"""
                try:
                    # Use eventlet-compatible non-blocking get
                    return self.pool.get(block=True, timeout=5)
                except eventlet.queue.Empty:
                    # Pool exhausted - create temporary connection
                    logger.warning(
                        event_type='pool_exhausted',
                        domain='database',
                        message='SQLite pool exhausted, creating temporary connection'
                    )
                    return self._create_connection()
                except Exception as e:
                    # Unexpected error getting connection
                    logger.error(
                        event_type='pool_get_error',
                        domain='database',
                        error=str(e),
                        exc_info=True
                    )
                    # Fallback to temp connection
                    return self._create_connection()

            def putconn(self, conn):
                """Return connection to pool or close if pool full"""
                try:
                    # Use eventlet-compatible non-blocking put
                    self.pool.put(conn, block=True, timeout=1)
                except eventlet.queue.Full:
                    # Pool is full - close the connection
                    logger.debug(
                        event_type='pool_full',
                        domain='database',
                        message='SQLite pool full, closing connection'
                    )
                    conn.close()
                except Exception as e:
                    # Unexpected error returning connection - close it
                    logger.warning(
                        event_type='pool_put_error',
                        domain='database',
                        error=str(e),
                        message='Error returning connection to pool, closing it'
                    )
                    try:
                        conn.close()
                    except Exception as close_error:
                        logger.error(
                            event_type='connection_close_error',
                            domain='database',
                            error=str(close_error)
                        )

            def _create_connection(self):
                conn = sqlite3.connect('skaila.db', timeout=30.0, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                return conn

        self.sqlite_pool = SQLitePool()
        logger.info(
            event_type='sqlite_pool_configured',
            domain='database',
            message='SQLite pool ottimizzato configurato',
            max_connections=10
        )

    def recreate_pool(self):
        """Chiude e ricrea il pool PostgreSQL"""
        if self.db_type == 'postgresql' and self.pool:
            logger.info(
                event_type='pool_recreating',
                domain='database',
                message='Chiudendo e ricreando il pool PostgreSQL'
            )
            try:
                self.pool.closeall()
            except Exception as e:
                logger.error(
                    event_type='pool_close_error',
                    domain='database',
                    message=f'Errore durante la chiusura del pool: {e}',
                    error=str(e),
                    exc_info=True
                )
            finally:
                self.pool = None
            self.setup_postgresql_pool()

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

                    logger.warning(
                        event_type='database_retry',
                        domain='database',
                        message=f'Database error (attempt {retry_count}/{max_retries}): {error_msg[:100]}',
                        retry_count=retry_count,
                        max_retries=max_retries,
                        error=error_msg[:100]
                    )

                    # IMPORTANTE: Chiudi connessione fallita
                    if conn:
                        try:
                            self.pool.putconn(conn, close=True)
                        except Exception as putconn_error:
                            # Log error but continue - connection is already dead
                            logger.debug(
                                event_type='failed_connection_cleanup',
                                domain='database',
                                error=str(putconn_error),
                                message='Error closing failed connection (expected)'
                            )
                        conn = None

                    # Ricrea pool SOLO se errore di connessione/SSL
                    if any(keyword in error_msg for keyword in ['ssl', 'connection', 'closed', 'eof', 'timeout']):
                        logger.warning(
                            event_type='neon_sleep_detected',
                            domain='database',
                            message='Neon sleep rilevato - ricreazione pool',
                            retry_count=retry_count
                        )
                        self.recreate_pool()

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
                        logger.error(
                            event_type='database_connection_failed',
                            domain='database',
                            message='Database connection failed definitivamente',
                            retry_count=retry_count,
                            max_retries=max_retries,
                            error=str(last_error) if last_error else 'Database unavailable',
                            exc_info=True
                        )
                        raise last_error if last_error else Exception("Database unavailable")

                except Exception as e:
                    # Non-database-specific error - log and raise
                    logger.error(
                        event_type='database_operation_error',
                        domain='database',
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                    
                    if conn:
                        try:
                            conn.rollback()
                            self.pool.putconn(conn)
                        except Exception as cleanup_error:
                            logger.warning(
                                event_type='connection_cleanup_failed',
                                domain='database',
                                error=str(cleanup_error)
                            )
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
            # SQLite usa ? - converti %s in ?
            adapted_query = query.replace('%s', '?')
            return adapted_query, params

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
                            logger.debug(
                                event_type='returning_fallback',
                                domain='database',
                                error=str(e),
                                message='Table has no id column, using rowcount instead'
                            )

                    # Fallback: usa rowcount (per ON CONFLICT o tabelle senza id)
                    return CursorProxy(lastrowid=0, rowcount=cursor.rowcount)

                # UPDATE/DELETE - ritorna rowcount
                return cursor.rowcount
            else:
                # SQLite - ritorna cursor originale per compatibilità
                return cursor

    def safe_alter_table(self, cursor, sql: str, table: str, column: str) -> bool:
        """
        Safely execute ALTER TABLE with proper transaction handling.
        Uses savepoints for PostgreSQL to prevent transaction abortion.
        
        Returns True if column was added, False if it already exists or failed.
        """
        try:
            if self.db_type == 'postgresql':
                # Use savepoint to isolate this operation
                savepoint_name = f"sp_{table}_{column}"
                cursor.execute(f"SAVEPOINT {savepoint_name}")
                try:
                    cursor.execute(sql)
                    cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    logger.debug(
                        event_type='migration_column_added',
                        domain='database',
                        table=table,
                        column=column
                    )
                    return True
                except Exception as e:
                    # Rollback to savepoint - this clears the error state
                    cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    error_str = str(e).lower()
                    if "already exists" in error_str or "duplicate" in error_str:
                        logger.debug(
                            event_type='migration_column_exists',
                            domain='database',
                            table=table,
                            column=column
                        )
                    else:
                        logger.warning(
                            event_type='migration_column_error',
                            domain='database',
                            table=table,
                            column=column,
                            error=str(e)
                        )
                    return False
            else:
                # SQLite doesn't have the same transaction issues
                cursor.execute(sql)
                logger.debug(
                    event_type='migration_column_added',
                    domain='database',
                    table=table,
                    column=column
                )
                return True
        except Exception as e:
            error_str = str(e).lower()
            if "already exists" in error_str or "duplicate" in error_str:
                logger.debug(
                    event_type='migration_column_exists',
                    domain='database',
                    table=table,
                    column=column
                )
            else:
                logger.warning(
                    event_type='migration_column_error',
                    domain='database',
                    table=table,
                    column=column,
                    error=str(e)
                )
            return False

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
                # Index already exists or creation failed - log but continue
                # This is expected on subsequent runs
                logger.debug(
                    event_type='index_already_exists',
                    domain='database',
                    index_sql=index_sql[:100],
                    error=str(e)
                )

        logger.info(
            event_type='indexes_optimized',
            domain='database',
            message='Database indexes optimized'
        )

# Istanza globale
db_manager = DatabaseManager()