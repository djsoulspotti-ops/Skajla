#!/usr/bin/env python3
"""
Script per creare 100 account beta test per SKAJLA
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import bcrypt
from services.database.database_manager import db_manager

NOMI = [
    "Marco", "Giulia", "Alessandro", "Francesca", "Lorenzo", "Chiara", "Matteo", "Sara",
    "Andrea", "Valentina", "Luca", "Martina", "Davide", "Elena", "Simone", "Alessia",
    "Federico", "Giorgia", "Riccardo", "Sofia", "Nicola", "Anna", "Gabriele", "Laura",
    "Tommaso", "Elisa", "Pietro", "Beatrice", "Giovanni", "Alice", "Filippo", "Camilla",
    "Daniele", "Greta", "Stefano", "Roberta", "Michele", "Ilaria", "Francesco", "Silvia",
    "Emanuele", "Federica", "Antonio", "Claudia", "Paolo", "Monica", "Roberto", "Veronica",
    "Fabio", "Cristina"
]

COGNOMI = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci",
    "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Giordano",
    "Mancini", "Rizzo", "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro", "Mariani",
    "Rinaldi", "Caruso", "Ferrara", "Galli", "Martini", "Leone", "Longo", "Gentile",
    "Martinelli", "Vitale", "Lombardo", "Serra", "Coppola", "De Santis", "D'Angelo", "Marchetti",
    "Parisi", "Villa", "Conte", "Ferraro", "Ferri", "Fabbri", "Bianco", "Marini",
    "Grasso", "Valentini"
]

CLASSI = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B"]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_beta_accounts():
    print("🚀 Creazione 100 account beta test...")
    
    accounts_created = []
    password = "beta2025"
    password_hash = hash_password(password)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        for i in range(1, 101):
            nome = NOMI[i % len(NOMI)]
            cognome = COGNOMI[i % len(COGNOMI)]
            classe = CLASSI[i % len(CLASSI)]
            
            username = f"beta{i:03d}"
            email = f"beta{i:03d}@test.skajla.it"
            
            try:
                cursor.execute(
                    "SELECT id FROM utenti WHERE email = %s OR username = %s",
                    (email, username)
                )
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute(
                        """UPDATE utenti SET password_hash = %s, attivo = true 
                           WHERE email = %s OR username = %s""",
                        (password_hash, email, username)
                    )
                    print(f"✅ Aggiornato: {username}")
                else:
                    cursor.execute(
                        """INSERT INTO utenti 
                           (username, email, password_hash, nome, cognome, classe, ruolo, attivo, primo_accesso)
                           VALUES (%s, %s, %s, %s, %s, %s, 'studente', true, false)""",
                        (username, email, password_hash, nome, cognome, classe)
                    )
                    print(f"✅ Creato: {username}")
                
                accounts_created.append({
                    "username": username,
                    "email": email,
                    "password": password,
                    "nome": nome,
                    "cognome": cognome,
                    "classe": classe
                })
                
            except Exception as e:
                print(f"❌ Errore {username}: {e}")
        
        conn.commit()
    
    print(f"\n{'='*60}")
    print(f"📊 RIEPILOGO: {len(accounts_created)} account creati/aggiornati")
    print(f"{'='*60}")
    print(f"\n🔐 CREDENZIALI BETA TEST:")
    print(f"   Email: beta001@test.skajla.it fino a beta100@test.skajla.it")
    print(f"   Password: {password}")
    print(f"{'='*60}")
    
    with open("docs/BETA_ACCOUNTS_LIST.md", "w") as f:
        f.write("# Account Beta Test SKAJLA\n\n")
        f.write("## Credenziali Rapide\n\n")
        f.write(f"**Password universale:** `{password}`\n\n")
        f.write("| # | Username | Email | Nome | Cognome | Classe |\n")
        f.write("|---|----------|-------|------|---------|--------|\n")
        for idx, acc in enumerate(accounts_created, 1):
            f.write(f"| {idx} | `{acc['username']}` | `{acc['email']}` | {acc['nome']} | {acc['cognome']} | {acc['classe']} |\n")
        f.write(f"\n---\n*Generato automaticamente*\n")
    
    print(f"\n📄 Lista completa salvata in: docs/BETA_ACCOUNTS_LIST.md")
    
    return accounts_created

if __name__ == "__main__":
    create_beta_accounts()
