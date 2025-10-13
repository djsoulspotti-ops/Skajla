
#!/usr/bin/env python3
"""
SKAILA Database Keep-Alive
Mantiene il database PostgreSQL Neon attivo con ping ogni 4 minuti
"""

import threading
import time
from database_manager import db_manager

class DatabaseKeepAlive:
    """Mantiene connessione database attiva"""
    
    def __init__(self, interval_seconds=240):  # 4 minuti
        self.interval = interval_seconds
        self.running = False
        self.thread = None
    
    def start(self):
        """Avvia keep-alive in background"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()
        print(f"✅ Database keep-alive attivo (ping ogni {self.interval}s)")
    
    def stop(self):
        """Ferma keep-alive"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Database keep-alive fermato")
    
    def _keep_alive_loop(self):
        """Loop che fa ping al database"""
        while self.running:
            try:
                # Ping semplice al database
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                    cursor.close()
                print("💚 Database keep-alive ping OK")
            except Exception as e:
                print(f"⚠️ Keep-alive ping failed: {e}")
            
            # Attendi 4 minuti prima del prossimo ping
            time.sleep(self.interval)

# Istanza globale
keep_alive = DatabaseKeepAlive()
