
"""
SKAILA - Database Upgrade per Scalabilità Produzione
Migrazione da SQLite a PostgreSQL per supportare 1000+ utenti
"""

import os
import sqlite3
import psycopg2
from psycopg2 import sql

def migrate_to_postgresql():
    """Migra il database da SQLite a PostgreSQL per scalabilità"""
    
    # Connessione PostgreSQL (per produzione)
    pg_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'skaila_prod'),
        'user': os.getenv('DB_USER', 'skaila_user'),
        'password': os.getenv('DB_PASSWORD', 'secure_password'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        # Connetti a PostgreSQL
        pg_conn = psycopg2.connect(**pg_config)
        pg_cursor = pg_conn.cursor()
        
        # Crea tabelle ottimizzate per PostgreSQL
        create_optimized_tables(pg_cursor)
        
        # Migra dati da SQLite se esiste
        if os.path.exists('skaila.db'):
            migrate_data_from_sqlite(pg_cursor)
        
        # Crea indici per performance
        create_performance_indexes(pg_cursor)
        
        pg_conn.commit()
        print("✅ Database PostgreSQL configurato per 1000+ utenti")
        
    except Exception as e:
        print(f"❌ Errore migrazione database: {e}")

def create_optimized_tables(cursor):
    """Crea tabelle ottimizzate per alta concorrenza"""
    
    # Tabella utenti con ottimizzazioni
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utenti (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            nome VARCHAR(100) NOT NULL,
            cognome VARCHAR(100) NOT NULL,
            classe VARCHAR(10),
            ruolo VARCHAR(20) DEFAULT 'studente',
            scuola VARCHAR(255),
            attivo BOOLEAN DEFAULT true,
            primo_accesso BOOLEAN DEFAULT true,
            ultimo_accesso TIMESTAMP,
            status_online BOOLEAN DEFAULT false,
            avatar VARCHAR(255) DEFAULT 'default.jpg',
            data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_token VARCHAR(255),
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabelle per gestione sessioni scalabile
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabella per gestione cache messaggi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_cache (
            id SERIAL PRIMARY KEY,
            chat_id INTEGER,
            last_message_id INTEGER,
            unread_count INTEGER DEFAULT 0,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_performance_indexes(cursor):
    """Crea indici per ottimizzare le query più frequenti"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_utenti_email ON utenti(email)",
        "CREATE INDEX IF NOT EXISTS idx_utenti_classe_ruolo ON utenti(classe, ruolo)",
        "CREATE INDEX IF NOT EXISTS idx_utenti_status_online ON utenti(status_online)",
        "CREATE INDEX IF NOT EXISTS idx_messaggi_chat_timestamp ON messaggi(chat_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_partecipanti_chat_user ON partecipanti_chat(utente_id)",
        "CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_subject ON ai_conversations(utente_id, subject_detected)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)

if __name__ == "__main__":
    migrate_to_postgresql()
