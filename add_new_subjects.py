
import sqlite3

def add_new_subject_chats():
    """Aggiunge le nuove chat per le materie specifiche"""
    conn = sqlite3.connect('skaila.db')
    cursor = conn.cursor()
    
    # Nuove chat da aggiungere
    new_chat_rooms = [
        ('📈 Digital Marketing', 'Strategie, campagne e trend del marketing digitale', 'tematica', ''),
        ('₿ Crypto e Blockchain', 'Discussioni su criptovalute, NFT e tecnologie blockchain', 'tematica', ''),
        ('⚖️ Fiscalità e Legalità', 'Consulenza fiscale, diritto e aspetti legali', 'tematica', ''),
        ('🌱 Sostenibilità Ambientale', 'Progetti green, economia circolare e ambiente', 'tematica', '')
    ]
    
    print("🔧 Aggiunta nuove chat tematiche...")
    
    for nome, descrizione, tipo, classe in new_chat_rooms:
        # Controlla se la chat esiste già
        existing = cursor.execute('SELECT id FROM chat WHERE nome = ?', (nome,)).fetchone()
        
        if not existing:
            cursor.execute('''
                INSERT INTO chat (nome, descrizione, tipo, classe)
                VALUES (?, ?, ?, ?)
            ''', (nome, descrizione, tipo, classe))
            
            chat_id = cursor.lastrowid
            print(f"✅ Creata chat: {nome} (ID: {chat_id})")
            
            # Aggiungi tutti gli utenti attivi a queste chat tematiche
            users = cursor.execute('SELECT id, ruolo FROM utenti WHERE attivo = 1').fetchall()
            
            for user_id, user_role in users:
                ruolo_chat = 'admin' if user_role == 'admin' else 'membro'
                
                cursor.execute('''
                    INSERT OR IGNORE INTO partecipanti_chat (chat_id, utente_id, ruolo_chat)
                    VALUES (?, ?, ?)
                ''', (chat_id, user_id, ruolo_chat))
            
            print(f"  → Aggiunti {len(users)} partecipanti alla chat {nome}")
        else:
            print(f"⚠️ Chat già esistente: {nome}")
    
    conn.commit()
    conn.close()
    print("🎉 Aggiornamento completato!")

if __name__ == "__main__":
    add_new_subject_chats()
