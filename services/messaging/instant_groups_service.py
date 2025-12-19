"""
Instant Groups Service
Gestione gruppi istantanei con scadenza e auto-cleanup
"""

from database_manager import db_manager
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class InstantGroupsService:
    """Servizio per gestione gruppi istantanei"""
    
    @staticmethod
    def init_instant_groups_schema():
        """Inizializza schema database per gruppi istantanei"""
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if db_manager.db_type == 'postgresql':
                    # Aggiungi colonne se non esistono
                    cursor.execute("""
                        DO $$ 
                        BEGIN
                            BEGIN
                                ALTER TABLE chat ADD COLUMN tipo_gruppo VARCHAR(50) DEFAULT 'permanente';
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                            
                            BEGIN
                                ALTER TABLE chat ADD COLUMN argomento VARCHAR(200);
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                            
                            BEGIN
                                ALTER TABLE chat ADD COLUMN scadenza TIMESTAMP;
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                            
                            BEGIN
                                ALTER TABLE chat ADD COLUMN ultimo_messaggio_at TIMESTAMP;
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                            
                            BEGIN
                                ALTER TABLE chat ADD COLUMN pubblico BOOLEAN DEFAULT FALSE;
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                            
                            BEGIN
                                ALTER TABLE chat ADD COLUMN attivo BOOLEAN DEFAULT TRUE;
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                            
                            BEGIN
                                ALTER TABLE chat ADD COLUMN scuola_id INTEGER;
                            EXCEPTION
                                WHEN duplicate_column THEN NULL;
                            END;
                        END $$;
                    """)
                    
                    # Crea indici
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
                    
                    # Tabella inviti
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
                    
                    # Aggiorna gruppi esistenti
                    cursor.execute("""
                        UPDATE chat 
                        SET tipo_gruppo = 'permanente', attivo = TRUE 
                        WHERE tipo_gruppo IS NULL
                    """)
                    
                conn.commit()
                logger.info("✅ Schema gruppi istantanei inizializzato")
                return True
                
            except Exception as e:
                logger.error(f"Errore inizializzazione schema: {e}")
                conn.rollback()
                return False
    
    @staticmethod
    def create_instant_group(
        nome: str,
        creatore_id: int,
        school_id: int,
        argomento: str,
        descrizione: str = "",
        durata_ore: int = 24,
        pubblico: bool = False,
        invitati: List[int] = None
    ) -> Optional[Dict]:
        """
        Crea un nuovo gruppo istantaneo
        
        Args:
            nome: Nome del gruppo
            creatore_id: ID utente creatore
            school_id: ID scuola
            argomento: Tag argomento (es: "matematica")
            descrizione: Descrizione opzionale
            durata_ore: Durata in ore (default 24h)
            pubblico: Se True, chiunque può unirsi
            invitati: Lista ID utenti da invitare (solo per gruppi privati)
        
        Returns:
            Dict con info gruppo creato o None se errore
        """
        
        # Validazioni
        if not nome or len(nome) < 3 or len(nome) > 100:
            raise ValueError("Nome gruppo deve essere 3-100 caratteri")
        
        if not argomento or len(argomento) < 2 or len(argomento) > 50:
            raise ValueError("Argomento deve essere 2-50 caratteri")
        
        if durata_ore < 1 or durata_ore > 168:  # Max 1 settimana
            raise ValueError("Durata deve essere 1-168 ore")
        
        # Calcola scadenza
        scadenza = datetime.utcnow() + timedelta(hours=durata_ore)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica rate limiting: max 5 gruppi attivi per utente
            cursor.execute("""
                SELECT COUNT(*) FROM chat
                WHERE creatore_id = %s 
                AND tipo_gruppo = 'istantaneo'
                AND attivo = TRUE
                AND (scadenza IS NULL OR scadenza > CURRENT_TIMESTAMP)
            """, (creatore_id,))
            
            active_count = cursor.fetchone()[0]
            if active_count >= 5:
                raise ValueError("Limite massimo 5 gruppi istantanei attivi raggiunto")
            
            # Crea gruppo
            cursor.execute("""
                INSERT INTO chat (
                    nome, descrizione, tipo, tipo_gruppo, argomento,
                    creatore_id, scuola_id, scadenza, pubblico, attivo,
                    data_creazione
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (
                nome, descrizione, 'istantaneo', 'istantaneo', argomento.lower(),
                creatore_id, school_id, scadenza, pubblico, True
            ))
            
            chat_id = cursor.fetchone()[0]
            
            # Aggiungi creatore come partecipante
            cursor.execute("""
                INSERT INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
                VALUES (%s, %s, %s)
            """, (chat_id, creatore_id, 'admin'))
            
            # Crea inviti se gruppo privato
            if not pubblico and invitati:
                for invitato_id in invitati[:50]:  # Max 50 inviti
                    try:
                        cursor.execute("""
                            INSERT INTO chat_inviti (chat_id, invitante_id, invitato_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (chat_id, invitato_id) DO NOTHING
                        """, (chat_id, creatore_id, invitato_id))
                    except:
                        pass  # Ignora duplicati
            
            conn.commit()
            
            logger.info(f"Gruppo istantaneo creato: {chat_id} - {nome}")
            
            return {
                'chat_id': chat_id,
                'nome': nome,
                'argomento': argomento,
                'scadenza': scadenza.isoformat(),
                'pubblico': pubblico,
                'invitati_count': len(invitati) if invitati else 0
            }
    
    @staticmethod
    def get_instant_groups(user_id: int, school_id: int) -> Dict[str, List]:
        """
        Ottieni gruppi istantanei disponibili per utente
        
        Returns:
            Dict con 'miei_gruppi', 'gruppi_partecipante', 'gruppi_pubblici'
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Gruppi creati dall'utente
            cursor.execute("""
                SELECT c.*, 
                       COUNT(DISTINCT pc.utente_id) as membri_count,
                       EXTRACT(EPOCH FROM (c.scadenza - CURRENT_TIMESTAMP))/3600 as ore_rimanenti
                FROM chat c
                LEFT JOIN partecipanti_chat pc ON c.id = pc.chat_id
                WHERE c.creatore_id = %s 
                AND c.tipo_gruppo = 'istantaneo'
                AND c.attivo = TRUE
                AND c.scadenza > CURRENT_TIMESTAMP
                GROUP BY c.id
                ORDER BY c.data_creazione DESC
            """, (user_id,))
            
            miei_gruppi = cursor.fetchall()
            
            # Gruppi dove sono partecipante (non creatore)
            cursor.execute("""
                SELECT c.*, 
                       u.nome as creatore_nome,
                       u.cognome as creatore_cognome,
                       COUNT(DISTINCT pc.utente_id) as membri_count,
                       EXTRACT(EPOCH FROM (c.scadenza - CURRENT_TIMESTAMP))/3600 as ore_rimanenti
                FROM chat c
                JOIN partecipanti_chat pc ON c.id = pc.chat_id
                JOIN utenti u ON c.creatore_id = u.id
                WHERE pc.utente_id = %s 
                AND c.creatore_id != %s
                AND c.tipo_gruppo = 'istantaneo'
                AND c.attivo = TRUE
                AND c.scadenza > CURRENT_TIMESTAMP
                GROUP BY c.id, u.nome, u.cognome
                ORDER BY c.data_creazione DESC
            """, (user_id, user_id))
            
            gruppi_partecipante = cursor.fetchall()
            
            # Gruppi pubblici disponibili (non ancora membro)
            cursor.execute("""
                SELECT c.*, 
                       u.nome as creatore_nome,
                       u.cognome as creatore_cognome,
                       COUNT(DISTINCT pc.utente_id) as membri_count,
                       EXTRACT(EPOCH FROM (c.scadenza - CURRENT_TIMESTAMP))/3600 as ore_rimanenti
                FROM chat c
                JOIN utenti u ON c.creatore_id = u.id
                LEFT JOIN partecipanti_chat pc ON c.id = pc.chat_id
                WHERE c.scuola_id = %s
                AND c.tipo_gruppo = 'istantaneo'
                AND c.pubblico = TRUE
                AND c.attivo = TRUE
                AND c.scadenza > CURRENT_TIMESTAMP
                AND c.id NOT IN (
                    SELECT chat_id FROM partecipanti_chat WHERE utente_id = %s
                )
                GROUP BY c.id, u.nome, u.cognome
                ORDER BY c.data_creazione DESC
                LIMIT 20
            """, (school_id, user_id))
            
            gruppi_pubblici = cursor.fetchall()
            
            return {
                'miei_gruppi': miei_gruppi or [],
                'gruppi_partecipante': gruppi_partecipante or [],
                'gruppi_pubblici': gruppi_pubblici or []
            }
    
    @staticmethod
    def join_instant_group(chat_id: int, user_id: int) -> bool:
        """Unisciti a gruppo istantaneo pubblico"""
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica che sia pubblico e attivo
            cursor.execute("""
                SELECT pubblico, attivo, scadenza 
                FROM chat 
                WHERE id = %s AND tipo_gruppo = 'istantaneo'
            """, (chat_id,))
            
            gruppo = cursor.fetchone()
            if not gruppo:
                raise ValueError("Gruppo non trovato")
            
            if not gruppo[0]:  # pubblico
                raise ValueError("Gruppo non pubblico")
            
            if not gruppo[1]:  # attivo
                raise ValueError("Gruppo non attivo")
            
            if gruppo[2] and gruppo[2] < datetime.utcnow():
                raise ValueError("Gruppo scaduto")
            
            # Verifica limite membri (max 50)
            cursor.execute("""
                SELECT COUNT(*) FROM partecipanti_chat WHERE chat_id = %s
            """, (chat_id,))
            
            if cursor.fetchone()[0] >= 50:
                raise ValueError("Gruppo pieno (max 50 membri)")
            
            # Aggiungi partecipante
            cursor.execute("""
                INSERT INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
                VALUES (%s, %s, 'membro')
                ON CONFLICT (chat_id, utente_id) DO NOTHING
            """, (chat_id, user_id))
            
            conn.commit()
            logger.info(f"Utente {user_id} unito a gruppo {chat_id}")
            return True
    
    @staticmethod
    def leave_instant_group(chat_id: int, user_id: int) -> bool:
        """Lascia gruppo istantaneo"""
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica che non sia il creatore
            cursor.execute("""
                SELECT creatore_id FROM chat WHERE id = %s
            """, (chat_id,))
            
            gruppo = cursor.fetchone()
            if gruppo and gruppo[0] == user_id:
                raise ValueError("Il creatore non può lasciare il gruppo (usa elimina)")
            
            # Rimuovi partecipante
            cursor.execute("""
                DELETE FROM partecipanti_chat 
                WHERE chat_id = %s AND utente_id = %s
            """, (chat_id, user_id))
            
            conn.commit()
            logger.info(f"Utente {user_id} ha lasciato gruppo {chat_id}")
            return True
    
    @staticmethod
    def delete_instant_group(chat_id: int, user_id: int) -> bool:
        """Elimina gruppo istantaneo (solo creatore)"""
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica che sia il creatore
            cursor.execute("""
                SELECT creatore_id, tipo_gruppo 
                FROM chat 
                WHERE id = %s
            """, (chat_id,))
            
            gruppo = cursor.fetchone()
            if not gruppo:
                raise ValueError("Gruppo non trovato")
            
            if gruppo[0] != user_id:
                raise ValueError("Solo il creatore può eliminare il gruppo")
            
            if gruppo[1] != 'istantaneo':
                raise ValueError("Solo gruppi istantanei possono essere eliminati")
            
            # Elimina gruppo (CASCADE eliminerà partecipanti e inviti)
            cursor.execute("""
                DELETE FROM chat WHERE id = %s
            """, (chat_id,))
            
            conn.commit()
            logger.info(f"Gruppo istantaneo {chat_id} eliminato da utente {user_id}")
            return True
    
    @staticmethod
    def cleanup_expired_groups() -> int:
        """
        Elimina gruppi istantanei scaduti
        Returns: numero gruppi eliminati
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Trova gruppi scaduti
            cursor.execute("""
                SELECT id, nome FROM chat
                WHERE tipo_gruppo = 'istantaneo'
                AND attivo = TRUE
                AND scadenza < CURRENT_TIMESTAMP
            """)
            
            expired = cursor.fetchall()
            
            if expired:
                # Elimina gruppi scaduti
                cursor.execute("""
                    DELETE FROM chat
                    WHERE tipo_gruppo = 'istantaneo'
                    AND attivo = TRUE
                    AND scadenza < CURRENT_TIMESTAMP
                """)
                
                conn.commit()
                logger.info(f"Eliminati {len(expired)} gruppi scaduti")
                return len(expired)
            
            return 0
    
    @staticmethod
    def cleanup_inactive_groups(hours: int = 24) -> int:
        """
        Elimina gruppi istantanei inattivi (senza messaggi da X ore)
        Returns: numero gruppi eliminati
        """
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM chat
                WHERE tipo_gruppo = 'istantaneo'
                AND attivo = TRUE
                AND (
                    ultimo_messaggio_at < CURRENT_TIMESTAMP - INTERVAL '%s hours'
                    OR (ultimo_messaggio_at IS NULL AND data_creazione < CURRENT_TIMESTAMP - INTERVAL '%s hours')
                )
                RETURNING id
            """, (hours, hours))
            
            deleted = cursor.fetchall()
            conn.commit()
            
            if deleted:
                logger.info(f"Eliminati {len(deleted)} gruppi inattivi")
            
            return len(deleted)


# Istanza globale
instant_groups_service = InstantGroupsService()
