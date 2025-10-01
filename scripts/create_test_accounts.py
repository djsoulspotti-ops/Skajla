
#!/usr/bin/env python3
"""
Script per creare account di test per SKAILA
"""

import sqlite3
import hashlib
from services.auth_service import auth_service

def create_test_accounts():
    """Crea account di test per demo SKAILA"""
    
    # Account di test da creare
    test_accounts = [
        {
            'username': 'studente_test',
            'email': 'studente.test@skaila.it',
            'password': 'test123',
            'nome': 'Marco',
            'cognome': 'Rossi',
            'ruolo': 'studente',
            'classe': '3A'
        },
        {
            'username': 'prof_test',
            'email': 'prof.test@skaila.it',
            'password': 'prof123',
            'nome': 'Maria',
            'cognome': 'Bianchi',
            'ruolo': 'professore',
            'classe': 'Matematica'
        },
        {
            'username': 'admin_test',
            'email': 'admin.test@skaila.it',
            'password': 'admin123',
            'nome': 'Giuseppe',
            'cognome': 'Verdi',
            'ruolo': 'admin',
            'classe': 'Dirigente'
        },
        {
            'username': 'dev_support',
            'email': 'dev.support@skaila.it',
            'password': 'dev2024!',
            'nome': 'Alex',
            'cognome': 'Developer',
            'ruolo': 'admin',
            'classe': 'Sviluppatore'
        }
    ]
    
    conn = sqlite3.connect('skaila.db')
    cursor = conn.cursor()
    
    # Trova scuola predefinita
    cursor.execute('SELECT id FROM scuole WHERE codice_pubblico = ?', ('DEFAULT_SCHOOL',))
    default_school = cursor.fetchone()
    
    if not default_school:
        print("⚠️ Nessuna scuola predefinita trovata. Creazione in corso...")
        cursor.execute('''
            INSERT INTO scuole (nome, codice_pubblico, indirizzo, citta, codice_invito_docenti, codice_dirigente)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Istituto Demo SKAILA', 'DEFAULT_SCHOOL', 'Via della Scuola, 1', 'Milano', 'PROF2024', 'DIR2024'))
        
        scuola_id = cursor.lastrowid
        print(f"✅ Scuola demo creata (ID: {scuola_id})")
    else:
        scuola_id = default_school[0]
    
    # Trova o crea classe 3A
    cursor.execute('SELECT id FROM classi WHERE nome = ? AND scuola_id = ?', ('3A', scuola_id))
    classe_result = cursor.fetchone()
    
    if not classe_result:
        cursor.execute('''
            INSERT INTO classi (nome, scuola_id, descrizione)
            VALUES (?, ?, ?)
        ''', ('3A', scuola_id, 'Classe terza sezione A'))
        classe_id = cursor.lastrowid
        print(f"✅ Classe 3A creata (ID: {classe_id})")
    else:
        classe_id = classe_result[0]
    
    conn.commit()
    conn.close()
    
    print("\n🚀 Creazione account di test...")
    
    for account in test_accounts:
        # Assegna scuola e classe appropriata
        account_scuola_id = scuola_id
        account_classe_id = classe_id if account['ruolo'] == 'studente' else None
        
        result = auth_service.create_user(
            username=account['username'],
            email=account['email'],
            password=account['password'],
            nome=account['nome'],
            cognome=account['cognome'],
            ruolo=account['ruolo'],
            classe=account['classe'],
            scuola_id=account_scuola_id,
            classe_id=account_classe_id
        )
        
        if result['success']:
            print(f"✅ Account creato: {account['email']} ({account['ruolo']})")
            
            # Aggiungi XP iniziali per demo
            if account['ruolo'] == 'studente':
                from gamification import gamification_system
                user_id = result['user_id']
                gamification_system.award_xp(user_id, 'welcome_bonus', 100, "Bonus benvenuto demo")
                print(f"  → XP bonus assegnati a {account['nome']}")
        else:
            print(f"❌ Errore creazione {account['email']}: {result['message']}")
    
    print(f"\n🎉 Account di test creati! Connettiti a SKAILA su http://0.0.0.0:5000")
    print("\n📧 CREDENZIALI DI ACCESSO:")
    print("👨‍🎓 Studente: studente.test@skaila.it / test123")
    print("👩‍🏫 Professore: prof.test@skaila.it / prof123") 
    print("👨‍💼 Admin: admin.test@skaila.it / admin123")
    print("👨‍💻 Sviluppatore: dev.support@skaila.it / dev2024!")

if __name__ == "__main__":
    create_test_accounts()
