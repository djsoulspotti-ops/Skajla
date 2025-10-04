
#!/usr/bin/env python3
"""
Test Login Credentials - SKAILA
Verifica tutte le credenziali disponibili
"""

import sys
sys.path.append('..')

from database_manager import db_manager
from services.auth_service import auth_service

def test_all_credentials():
    """Testa tutte le credenziali disponibili"""
    
    credentials = [
        ('studente.test@skaila.it', 'test123', 'Studente'),
        ('prof.test@skaila.it', 'prof123', 'Professore'),
        ('admin.test@skaila.it', 'admin123', 'Admin'),
        ('dev.support@skaila.it', 'dev2024!', 'Developer'),
        ('founder@skaila.it', 'founder123', 'Founder'),
        ('alice@test.skaila.it', 'test123', 'Alice'),
        ('prof@test.skaila.it', 'prof123', 'Prof Demo'),
    ]
    
    print("🧪 Test Login Credentials SKAILA\n")
    print("=" * 60)
    
    working_creds = []
    failed_creds = []
    
    for email, password, name in credentials:
        print(f"\n📧 Testing: {name} ({email})")
        print(f"🔑 Password: {password}")
        
        try:
            user = auth_service.authenticate_user(email, password)
            
            if user:
                print(f"✅ LOGIN SUCCESSFUL")
                print(f"   👤 {user['nome']} {user['cognome']}")
                print(f"   🎭 Ruolo: {user['ruolo']}")
                working_creds.append((email, password, name))
            else:
                print(f"❌ LOGIN FAILED")
                failed_creds.append((email, password, name))
                
                # Verifica se utente esiste
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    if db_manager.db_type == 'postgresql':
                        cursor.execute('SELECT id, attivo FROM utenti WHERE email = %s', (email,))
                    else:
                        cursor.execute('SELECT id, attivo FROM utenti WHERE email = ?', (email,))
                    
                    user_exists = cursor.fetchone()
                    if user_exists:
                        print(f"   ⚠️ Utente esiste (ID: {user_exists[0]}, Attivo: {user_exists[1]})")
                    else:
                        print(f"   ❌ Utente non trovato nel database")
                        
        except Exception as e:
            print(f"💥 ERROR: {e}")
            failed_creds.append((email, password, name))
    
    print("\n" + "=" * 60)
    print(f"\n📊 RISULTATI:")
    print(f"✅ Credenziali funzionanti: {len(working_creds)}")
    print(f"❌ Credenziali non funzionanti: {len(failed_creds)}")
    
    if working_creds:
        print(f"\n🎉 CREDENZIALI VALIDE:")
        for email, password, name in working_creds:
            print(f"   {name}: {email} / {password}")
    
    if failed_creds:
        print(f"\n⚠️ CREDENZIALI DA VERIFICARE:")
        for email, password, name in failed_creds:
            print(f"   {name}: {email} / {password}")

if __name__ == "__main__":
    test_all_credentials()
