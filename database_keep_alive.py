"""
SKAILA Database Keep-Alive + Storage Auto-Cleanup
Mantiene database PostgreSQL attivo (evita Neon sleep) + pulizia storage automatica
"""

import threading
import time
from database_manager import db_manager

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

keep_alive = KeepAliveService()