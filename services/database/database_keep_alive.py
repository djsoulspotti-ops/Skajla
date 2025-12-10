"""
SKAJLA Database Keep-Alive + Storage Auto-Cleanup
Mantiene database PostgreSQL attivo (evita Neon sleep) + pulizia storage automatica
"""

import threading
import time
from database_manager import db_manager
from datetime import datetime, timedelta

class KeepAliveService:
    """Servizio keep-alive database + storage cleanup"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.cleanup_thread = None

    def start(self):
        """Avvia keep-alive e storage cleanup"""
        if self.running:
            return

        self.running = True

        # Thread keep-alive database (ogni 2 min)
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()

        # Thread storage cleanup (ogni 24h)
        self.cleanup_thread = threading.Thread(target=self._storage_cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        print("✅ Keep-alive + Storage cleanup attivati")

    def _keep_alive_loop(self):
        """Loop keep-alive database"""
        consecutive_errors = 0
        max_errors = 3

        while self.running:
            try:
                # Esegui una query semplice per mantenere attiva la connessione
                db_manager.query('SELECT 1', one=True)
                consecutive_errors = 0  # Resetta il contatore degli errori in caso di successo
                print("💚 Database keep-alive ping OK")
            except Exception as e:
                consecutive_errors += 1
                print(f"⚠️ Keep-alive error ({consecutive_errors}/{max_errors}): {e}")

                # Se si verificano troppi errori consecutivi, tenta di ricreare il pool di connessioni
                if consecutive_errors >= max_errors:
                    print("🔄 Troppi errori - forzando ricreazione pool...")
                    try:
                        db_manager.recreate_pool()
                        consecutive_errors = 0  # Resetta il contatore dopo il successo della ricreazione
                    except Exception as pool_error:
                        print(f"❌ Errore ricreazione pool: {pool_error}")

            # Ping ogni 2 minuti (più aggressivo per Neon free tier che va in sleep dopo 5 min)
            time.sleep(120)

    def _storage_cleanup_loop(self):
        """Loop pulizia storage automatica (24h)"""
        while self.running:
            try:
                # Attendi 24h prima del primo cleanup
                time.sleep(86400)  # 24 ore

                # Esegui cleanup storage
                from teaching_materials_manager import materials_manager
                storage_status = materials_manager.check_storage_usage()

                if storage_status.get('warning'):
                    print(f"🧹 Storage cleanup: {storage_status['cleaned_files']} file rimossi")
                else:
                    print(f"✅ Storage OK: {storage_status['total_gb']}/{storage_status['limit_gb']} GB")

            except Exception as e:
                print(f"⚠️ Storage cleanup error: {e}")

    def cleanup_old_data(self):
        """Pulizia dati vecchi per ottimizzare storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=90)

            # Pulisci log vecchi
            db_manager.execute('''
                DELETE FROM ai_conversations 
                WHERE timestamp < %s
            ''', (cutoff_date,))

            db_manager.execute('''
                DELETE FROM messaggi 
                WHERE timestamp < %s
            ''', (cutoff_date,))

            print("🧹 Cleanup storage completato")
        except Exception as e:
            print(f"⚠️ Errore cleanup storage: {e}")

    def check_storage_usage(self) -> dict:
        """Verifica utilizzo storage database"""
        try:
            # Per PostgreSQL
            if db_manager.db_type == 'postgresql':
                result = db_manager.query('''
                    SELECT pg_database_size(current_database()) as size_bytes
                ''', one=True)

                if result:
                    size_mb = result['size_bytes'] / (1024 * 1024)
                    # Neon free tier: 512 MB limit
                    percentage_used = (size_mb / 512) * 100

                    return {
                        'total_size_mb': round(size_mb, 2),
                        'percentage_used': round(percentage_used, 2),
                        'status': 'ok' if percentage_used < 80 else 'warning'
                    }

            # Fallback per SQLite
            import os
            if os.path.exists('skaila.db'):
                size_bytes = os.path.getsize('skaila.db')
                size_mb = size_bytes / (1024 * 1024)
                return {
                    'total_size_mb': round(size_mb, 2),
                    'percentage_used': 0,
                    'status': 'ok'
                }

            return {'total_size_mb': 0, 'percentage_used': 0, 'status': 'unknown'}

        except Exception as e:
            print(f"⚠️ Errore check storage: {e}")
            return {'total_size_mb': 0, 'percentage_used': 0, 'status': 'error'}


keep_alive = KeepAliveService()