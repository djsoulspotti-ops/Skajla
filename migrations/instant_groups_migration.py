"""
Database Migration: Instant Groups Support
Aggiunge supporto per gruppi istantanei con scadenza e auto-cleanup
"""

from database_manager import db_manager
from datetime import datetime

def upgrade():
    """Applica migration per gruppi istantanei"""
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("🔧 Applicando migration per gruppi istantanei...")
        
        # 1. Aggiungi colonne alla tabella chat
        if db_manager.db_type == 'postgresql':
            # PostgreSQL: usa ALTER TABLE IF NOT EXISTS per sicurezza
            cursor.execute("""
                ALTER TABLE chat 
                ADD COLUMN IF NOT EXISTS tipo_gruppo VARCHAR(50) DEFAULT 'permanente',
                ADD COLUMN IF NOT EXISTS argomento VARCHAR(200),
                ADD COLUMN IF NOT EXISTS scadenza TIMESTAMP,
                ADD COLUMN IF NOT EXISTS ultimo_messaggio_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS pubblico BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS attivo BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS scuola_id INTEGER
            """)
            print("✅ Colonne aggiunte a tabella chat")
            
            # 2. Crea indici per performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_tipo_gruppo 
                ON chat(tipo_gruppo, attivo) 
                WHERE attivo = TRUE
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_scadenza 
                ON chat(scadenza) 
                WHERE scadenza IS NOT NULL
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_argomento 
                ON chat(argomento) 
                WHERE argomento IS NOT NULL
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_scuola 
                ON chat(scuola_id) 
                WHERE scuola_id IS NOT NULL
            """)
            print("✅ Indici creati per performance")
            
            # 3. Crea tabella inviti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_inviti (
                    id SERIAL PRIMARY KEY,
                    chat_id INTEGER NOT NULL REFERENCES chat(id) ON DELETE CASCADE,
                    invitante_id INTEGER NOT NULL REFERENCES utenti(id),
                    invitato_id INTEGER NOT NULL REFERENCES utenti(id),
                    stato VARCHAR(20) DEFAULT 'pending',
                    data_invito TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_risposta TIMESTAMP,
                    
                    UNIQUE(chat_id, invitato_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inviti_invitato 
                ON chat_inviti(invitato_id, stato) 
                WHERE stato = 'pending'
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inviti_chat 
                ON chat_inviti(chat_id, stato)
            """)
            print("✅ Tabella chat_inviti creata")
            
            # 4. Aggiorna gruppi esistenti come permanenti
            cursor.execute("""
                UPDATE chat 
                SET tipo_gruppo = 'permanente', 
                    attivo = TRUE 
                WHERE tipo_gruppo IS NULL
            """)
            print("✅ Gruppi esistenti marcati come permanenti")
            
        else:
            # SQLite: gestione più semplice
            # Nota: SQLite non supporta ALTER TABLE ADD COLUMN IF NOT EXISTS
            # quindi usiamo try/except
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN tipo_gruppo TEXT DEFAULT 'permanente'")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN argomento TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN scadenza TIMESTAMP")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN ultimo_messaggio_at TIMESTAMP")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN pubblico BOOLEAN DEFAULT 0")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN attivo BOOLEAN DEFAULT 1")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE chat ADD COLUMN scuola_id INTEGER")
            except:
                pass
            
            # Tabella inviti SQLite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_inviti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    invitante_id INTEGER NOT NULL,
                    invitato_id INTEGER NOT NULL,
                    stato TEXT DEFAULT 'pending',
                    data_invito TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_risposta TIMESTAMP,
                    
                    FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE,
                    FOREIGN KEY (invitante_id) REFERENCES utenti(id),
                    FOREIGN KEY (invitato_id) REFERENCES utenti(id),
                    UNIQUE(chat_id, invitato_id)
                )
            """)
            print("✅ Schema SQLite aggiornato")
        
        conn.commit()
        print("✅ Migration completata con successo!")
        
        return True

def downgrade():
    """Rollback migration (opzionale)"""
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("🔧 Rollback migration gruppi istantanei...")
        
        if db_manager.db_type == 'postgresql':
            # Rimuovi tabella inviti
            cursor.execute("DROP TABLE IF EXISTS chat_inviti CASCADE")
            
            # Rimuovi indici
            cursor.execute("DROP INDEX IF EXISTS idx_chat_tipo_gruppo")
            cursor.execute("DROP INDEX IF EXISTS idx_chat_scadenza")
            cursor.execute("DROP INDEX IF EXISTS idx_chat_argomento")
            cursor.execute("DROP INDEX IF EXISTS idx_chat_scuola")
            
            # Rimuovi colonne (PostgreSQL non supporta DROP COLUMN IF EXISTS in una sola query)
            try:
                cursor.execute("ALTER TABLE chat DROP COLUMN tipo_gruppo")
                cursor.execute("ALTER TABLE chat DROP COLUMN argomento")
                cursor.execute("ALTER TABLE chat DROP COLUMN scadenza")
                cursor.execute("ALTER TABLE chat DROP COLUMN ultimo_messaggio_at")
                cursor.execute("ALTER TABLE chat DROP COLUMN pubblico")
                cursor.execute("ALTER TABLE chat DROP COLUMN attivo")
            except:
                pass
        else:
            # SQLite: rimuovi solo tabella inviti (non supporta DROP COLUMN)
            cursor.execute("DROP TABLE IF EXISTS chat_inviti")
        
        conn.commit()
        print("✅ Rollback completato")

if __name__ == '__main__':
    # Esegui migration
    upgrade()
