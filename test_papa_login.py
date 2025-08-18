
#!/usr/bin/env python3
import sqlite3
import bcrypt

def verify_password(password, hashed):
    """Verifica password con bcrypt"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        # Fallback per hash SHA-256 esistenti durante migrazione
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed

def test_papa_login():
    """Test completo del login di papà"""
    conn = sqlite3.connect('skaila.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🧪 Test login papà...")
    
    # Test credenziali
    email = 'papa@skaila.it'
    password = 'papa123'
    
    print(f"📧 Email di test: {email}")
    print(f"🔑 Password di test: {password}")
    
    # Trova utente
    papa = cursor.execute('SELECT * FROM utenti WHERE email = ?', (email,)).fetchone()
    
    if not papa:
        print("❌ ERRORE: Account papà non trovato!")
        conn.close()
        return False
    
    print(f"✅ Utente trovato: {papa['nome']} {papa['cognome']}")
    print(f"🆔 ID: {papa['id']}")
    print(f"👤 Username: {papa['username']}")
    print(f"🔒 Account attivo: {'Sì' if papa['attivo'] else 'No'}")
    print(f"🎭 Ruolo: {papa['ruolo']}")
    
    # Test password
    stored_hash = papa['password_hash']
    print(f"\n🔍 Hash memorizzato: {stored_hash[:50]}...")
    
    # Test con bcrypt
    try:
        password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        print(f"✅ Test bcrypt: {'✅ SUCCESSO' if password_valid else '❌ FALLITO'}")
    except Exception as e:
        print(f"❌ Errore bcrypt: {e}")
        password_valid = False
    
    # Test con SHA-256 fallback
    if not password_valid:
        import hashlib
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        password_valid = sha256_hash == stored_hash
        print(f"🔄 Test SHA-256 fallback: {'✅ SUCCESSO' if password_valid else '❌ FALLITO'}")
    
    # Verifica finale
    can_login = password_valid and papa['attivo'] == 1
    
    print(f"\n{'🎉' if can_login else '❌'} RISULTATO FINALE:")
    print(f"{'✅' if password_valid else '❌'} Password corretta: {password_valid}")
    print(f"{'✅' if papa['attivo'] else '❌'} Account attivo: {papa['attivo'] == 1}")
    print(f"{'🚀' if can_login else '🚫'} LOGIN POSSIBILE: {can_login}")
    
    if can_login:
        print(f"\n📝 CREDENZIALI FUNZIONANTI:")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
    else:
        print(f"\n🔧 Il login non funziona! Controllare configurazione.")
    
    conn.close()
    return can_login

if __name__ == "__main__":
    try:
        test_papa_login()
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
