"""
SKAJLA - Subject Groups Initializer
Automatically creates predefined subject-based chat groups for classes
"""

from services.database.database_manager import DatabaseManager

db_manager = DatabaseManager()

# Predefined subject groups for Italian schools
PREDEFINED_SUBJECTS = [
    {'nome': 'Matematica', 'icon': '📐'},
    {'nome': 'Fisica', 'icon': '⚡'},
    {'nome': 'Scienze', 'icon': '🔬'},
    {'nome': 'Italiano', 'icon': '📚'},
    {'nome': 'Inglese', 'icon': '🌍'},
    {'nome': 'Storia', 'icon': '🏛️'}
]


def initialize_subject_groups_for_class(school_id: int, classe: str) -> list:
    """
    Initialize all predefined subject chat groups for a specific class
    
    Args:
        school_id: The school ID
        classe: The class identifier (e.g., "5A", "3B")
    
    Returns:
        List of created chat group IDs
    
    Example:
        >>> initialize_subject_groups_for_class(1, "5A")
        [101, 102, 103, 104, 105, 106]
    """
    created_groups = []
    
    for subject in PREDEFINED_SUBJECTS:
        # Check if subject group already exists for this class
        # Match on nome pattern + classe + tipo to avoid duplicates
        group_name = f"{subject['icon']} {subject['nome']} - Classe {classe}"
        existing = db_manager.query('''
            SELECT id FROM chat
            WHERE scuola_id = %s 
            AND classe = %s 
            AND tipo = 'materia'
            AND nome LIKE %s
        ''', (school_id, classe, f"%{subject['nome']}%"), one=True)
        
        if existing:
            print(f"✅ Gruppo materia '{subject['nome']}' già esistente per classe {classe}")
            created_groups.append(existing['id'])
            continue
        
        # Create subject group
        result = db_manager.query('''
            INSERT INTO chat (nome, scuola_id, classe, tipo, data_creazione)
            VALUES (%s, %s, %s, 'materia', CURRENT_TIMESTAMP)
            RETURNING id
        ''', (group_name, school_id, classe), one=True)
        
        if result:
            chat_id = result['id']
            created_groups.append(chat_id)
            print(f"✅ Creato gruppo materia: {subject['nome']} per classe {classe} (ID: {chat_id})")
        else:
            print(f"❌ Errore creando gruppo {subject['nome']} per classe {classe}")
    
    return created_groups


def add_student_to_subject_groups(user_id: int, school_id: int, classe: str) -> bool:
    """
    Add a student to all subject groups for their class
    
    Args:
        user_id: The student's user ID
        school_id: The school ID
        classe: The class identifier
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> add_student_to_subject_groups(42, 1, "5A")
        True
    """
    try:
        # Get all subject groups for this class
        subject_groups = db_manager.query('''
            SELECT id, nome FROM chat
            WHERE scuola_id = %s 
            AND classe = %s 
            AND tipo = 'materia'
        ''', (school_id, classe))
        
        if not subject_groups:
            print(f"⚠️ Nessun gruppo materia trovato per classe {classe}, li creo ora...")
            initialize_subject_groups_for_class(school_id, classe)
            # Retry query
            subject_groups = db_manager.query('''
                SELECT id, nome FROM chat
                WHERE scuola_id = %s 
                AND classe = %s 
                AND tipo = 'materia'
            ''', (school_id, classe))
        
        # Add student to each subject group
        for group in subject_groups:
            # Check if already a participant
            existing = db_manager.query('''
                SELECT 1 FROM partecipanti_chat
                WHERE chat_id = %s AND utente_id = %s
            ''', (group['id'], user_id), one=True)
            
            if not existing:
                db_manager.execute('''
                    INSERT INTO partecipanti_chat (chat_id, utente_id, joined_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                ''', (group['id'], user_id))
                print(f"✅ Studente {user_id} aggiunto a gruppo: {group['nome']}")
            else:
                print(f"ℹ️ Studente {user_id} già nel gruppo: {group['nome']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Errore aggiungendo studente ai gruppi materia: {e}")
        return False


def initialize_all_subject_groups_for_school(school_id: int) -> dict:
    """
    Initialize subject groups for all existing classes in a school
    Useful for retroactive initialization
    
    Args:
        school_id: The school ID
    
    Returns:
        Dictionary with statistics
    
    Example:
        >>> initialize_all_subject_groups_for_school(1)
        {'classes_processed': 5, 'groups_created': 30}
    """
    # Get all unique classes in the school
    classes = db_manager.query('''
        SELECT DISTINCT classe FROM utenti
        WHERE scuola_id = %s 
        AND classe IS NOT NULL 
        AND classe != ''
        AND ruolo = 'studente'
    ''', (school_id,))
    
    stats = {
        'classes_processed': 0,
        'groups_created': 0
    }
    
    for class_record in classes:
        classe = class_record['classe']
        created = initialize_subject_groups_for_class(school_id, classe)
        stats['classes_processed'] += 1
        stats['groups_created'] += len(created)
        print(f"✅ Classe {classe}: {len(created)} gruppi inizializzati")
    
    return stats


__all__ = [
    'PREDEFINED_SUBJECTS',
    'initialize_subject_groups_for_class',
    'add_student_to_subject_groups',
    'initialize_all_subject_groups_for_school'
]
