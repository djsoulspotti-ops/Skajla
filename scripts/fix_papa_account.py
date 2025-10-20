
#!/usr/bin/env python3
import sqlite3
import hashlib
import bcrypt

def hash_password(password):
    """Hash sicuro con bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def fix_papa_account():
    """Verifica e ripara l'account di papà"""
    conn = sqlite3.connect('skaila.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🔍 Verifica account papà...")
    
    # Controlla se l'account esiste
    papa = cursor.execute('SELECT * FROM utenti WHERE email = %s', ('papa@skaila.it',)).fetchone()
    
    if not papa:
        print("❌ Account papà non trovato! Creazione in corso...")
        
        # Crea account papà
        papa_password = hash_password('papa123')
        cursor.execute('''
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo, attivo, primo_accesso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', ('papa', 'papa@skaila.it', papa_password, 'Papà', 'Famiglia', 'genitore', 1, 0))
        
        print("✅ Account papà creato con successo!")
        
    else:
        print(f"✅ Account trovato - ID: {papa['id']}, Nome: {papa['nome']}")
        print(f"📧 Email: {papa['email']}")
        print(f"👤 Username: {papa['username']}")
        print(f"🔒 Attivo: {'Sì' if papa['attivo'] else 'No'}")
        print(f"🎭 Ruolo: {papa['ruolo']}")
        
        # Verifica se l'account è attivo
        if not papa['attivo']:
            print("⚠️ Account disattivato! Riattivazione...")
            cursor.execute('UPDATE utenti SET attivo = 1 WHERE id = %s', (papa['id'],))
            print("✅ Account riattivato!")
        
        # Reset password per sicurezza
        print("🔄 Reset password a 'papa123'...")
        new_password = hash_password('papa123')
        cursor.execute('UPDATE utenti SET password_hash = %s WHERE id = %s', (new_password, papa['id']))
        print("✅ Password resettata!")
    
    # Verifica credenziali finali
    papa_verificato = cursor.execute('SELECT * FROM utenti WHERE email = %s', ('papa@skaila.it',)).fetchone()
    
    if papa_verificato and papa_verificato['attivo']:
        print("\n🎉 ACCOUNT PAPÀ PRONTO!")
        print("📧 Email: papa@skaila.it")
        print("🔑 Password: papa123")
        print("✅ Account attivo e funzionante")
        
        # Test password
        test_password = hash_password('papa123')
        print(f"\n🔍 Test password: {'✅ Corretta' if bcrypt.checkpw('papa123'.encode(), papa_verificato['password_hash'].encode()) else '❌ Errore'}")
        
    else:
        print("❌ Errore nella verifica finale!")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        fix_papa_account()
    except Exception as e:
        print(f"❌ Errore: {e}")
