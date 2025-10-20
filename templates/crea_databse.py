import sqlite3

# Connessione (crea il file skaila.db se non esiste)
conn = sqlite3.connect("skaila.db")
cursor = conn.cursor()

# Creazione tabella utenti
cursor.execute("""
CREATE TABLE IF NOT EXISTS utenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

# Inserire un utente di test
cursor.execute("""
INSERT OR IGNORE INTO utenti (nome, email, password)
VALUES (%s, %s, %s)
""", ("Daniele", "danis@gmail.com", "1234"))

conn.commit()
conn.close()

print("✅ Database creato e utente di prova inserito!")