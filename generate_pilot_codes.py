from services.school_codes_manager import school_codes_manager
from services.database.database_manager import db_manager

# Assicuriamoci che i codici siano generati
print("🔄 Generazione codici in corso...")
result = school_codes_manager.generate_initial_codes()

# Prendiamo i codici della prima scuola (Scuola Pilota)
codes = school_codes_manager.get_all_codes()

if codes:
    pilot_school = codes[0]  # La prima scuola
    
    print("\n" + "="*50)
    print("🚀  CODICI PER IL TEST PILOTA (3 CLASSI)  🚀")
    print("="*50)
    print(f"\nNome Scuola (Sistema): {pilot_school['school_name']}")
    print(f"\n🔐 CODICE PER GLI STUDENTI:   {pilot_school['school_code']}")
    print(f"   (Da scrivere alla lavagna)")
    print(f"\n👨‍🏫 CODICE PER I PROFESSORI:  {pilot_school['teacher_code']}")
    print(f"\n👔 CODICE PER IL PRESIDE:    {pilot_school['director_code']}")
    print("\n" + "="*50)
    print("\nISTRUZIONI PER IL TEST:")
    print("1. Gli studenti vanno su: https://skajla.today/register")
    print(f"2. Inseriscono il Codice Scuola: {pilot_school['school_code']}")
    print("3. Nel campo 'Classe', scrivono il nome della loro classe (es: 3A, 4B, 5C)")
    print("4. Il sistema li raggrupperà automaticamente nella classe giusta.")
    print("="*50 + "\n")
else:
    print("❌ Errore: Nessun codice generato.")
