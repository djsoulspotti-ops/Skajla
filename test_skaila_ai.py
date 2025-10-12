"""
Test SKAILA AI System
Esempio di interazione completa con l'AI Brain
"""

from skaila_ai_brain import skaila_brain
from skaila_quiz_manager import quiz_manager

def test_ai_interaction():
    """Test interazione AI completa"""
    
    # Simula utente ID 1 (deve esistere nel database)
    user_id = 1
    
    print("=" * 60)
    print("🤖 TEST SKAILA AI BRAIN ENGINE")
    print("=" * 60)
    
    # Test 1: Richiesta aiuto matematica
    print("\n📝 TEST 1: Richiesta aiuto matematica")
    print("-" * 60)
    
    message = "Ciao, ho bisogno di aiuto con la matematica"
    context = skaila_brain.analyze_student_context(user_id, message)
    response = skaila_brain.generate_intelligent_response(context)
    
    print(f"👤 Studente: {message}")
    print(f"\n🤖 SKAILA AI: {response}")
    
    # Test 2: Richiesta quiz
    print("\n\n📝 TEST 2: Richiesta quiz")
    print("-" * 60)
    
    message = "Voglio fare un quiz di matematica"
    context = skaila_brain.analyze_student_context(user_id, message)
    response = skaila_brain.generate_intelligent_response(context)
    
    print(f"👤 Studente: {message}")
    print(f"\n🤖 SKAILA AI: {response}")
    
    # Test 3: Quiz adattivo
    print("\n\n📝 TEST 3: Generazione quiz adattivo")
    print("-" * 60)
    
    quiz = quiz_manager.get_adaptive_quiz(user_id, 'matematica')
    
    if quiz:
        print(f"📚 Materia: {quiz['subject']}")
        print(f"🎯 Argomento: {quiz['topic']}")
        print(f"⭐ Difficoltà: {quiz['difficulty']}")
        print(f"\n❓ Domanda: {quiz['question']}")
        print(f"\nOpzioni:")
        for letter, option in quiz['options'].items():
            print(f"  {letter}) {option}")
        print(f"\n✅ Risposta corretta: {quiz['correct_answer']}")
        print(f"💡 Spiegazione: {quiz['explanation']}")
        print(f"🎁 XP Reward: {quiz['xp_reward']}")
    else:
        print("❌ Nessun quiz trovato")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETATI!")
    print("=" * 60)

if __name__ == '__main__':
    test_ai_interaction()
