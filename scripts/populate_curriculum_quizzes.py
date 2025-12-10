"""
SKAJLA - Script per popolare il database con quiz del programma ministeriale italiano
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database.database_manager import DatabaseManager
from scripts.italian_curriculum_quizzes import get_all_quizzes

db_manager = DatabaseManager()

def populate_curriculum_quizzes():
    """Popola il database con i quiz allineati ai programmi ministeriali"""
    
    all_quizzes = get_all_quizzes()
    total_inserted = 0
    
    print("=" * 60)
    print("SKAJLA - Inserimento Quiz Programmi Ministeriali Italiani")
    print("=" * 60)
    
    for level, subjects in all_quizzes.items():
        print(f"\n📚 {level.upper().replace('_', ' ')}")
        print("-" * 40)
        
        for subject, quizzes in subjects.items():
            inserted = 0
            
            for quiz in quizzes:
                try:
                    existing = db_manager.query('''
                        SELECT id FROM quiz_bank 
                        WHERE question = %s AND subject = %s
                    ''', (quiz['question'], quiz['subject']), one=True)
                    
                    if existing:
                        continue
                    
                    db_manager.execute('''
                        INSERT INTO quiz_bank 
                        (subject, topic, difficulty, question, option_a, option_b, 
                         option_c, option_d, correct_answer, explanation, xp_reward,
                         grade_level, grade_year, learning_objective, approved, times_used)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, 0)
                    ''', (
                        quiz['subject'],
                        quiz['topic'],
                        quiz['difficulty'],
                        quiz['question'],
                        quiz['option_a'],
                        quiz['option_b'],
                        quiz['option_c'],
                        quiz['option_d'],
                        quiz['correct_answer'],
                        quiz['explanation'],
                        quiz['xp_reward'],
                        quiz['grade_level'],
                        quiz.get('grade_year'),
                        quiz.get('learning_objective', '')
                    ))
                    inserted += 1
                    
                except Exception as e:
                    print(f"  ❌ Errore: {e}")
            
            total_inserted += inserted
            print(f"  ✅ {subject.capitalize()}: {inserted} nuovi quiz inseriti")
    
    print("\n" + "=" * 60)
    print(f"🎉 COMPLETATO: {total_inserted} quiz inseriti nel database!")
    print("=" * 60)
    
    stats = db_manager.query('''
        SELECT grade_level, subject, COUNT(*) as count
        FROM quiz_bank
        GROUP BY grade_level, subject
        ORDER BY grade_level, subject
    ''')
    
    print("\n📊 STATISTICHE DATABASE QUIZ:")
    print("-" * 40)
    current_level = None
    for row in stats:
        if row['grade_level'] != current_level:
            current_level = row['grade_level']
            print(f"\n{current_level.upper() if current_level else 'NON SPECIFICATO'}:")
        print(f"  • {row['subject']}: {row['count']} quiz")
    
    total = db_manager.query('SELECT COUNT(*) as total FROM quiz_bank', one=True)
    print(f"\n📈 TOTALE QUIZ NEL DATABASE: {total['total']}")

if __name__ == '__main__':
    populate_curriculum_quizzes()
