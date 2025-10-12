"""
SKAILA AI Routes - API Backend per Chatbot AI
Gestisce interazioni AI, quiz, e progressi studenti
"""

from flask import Blueprint, request, jsonify, session
from skaila_ai_brain import skaila_brain
from skaila_quiz_manager import quiz_manager
from gamification import gamification_system
from database_manager import db_manager
from datetime import datetime

ai_bp = Blueprint('skaila_ai', __name__)

@ai_bp.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Endpoint principale chat AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Messaggio vuoto'}), 400
    
    user_id = session['user_id']
    
    try:
        # Analizza contesto studente
        context = skaila_brain.analyze_student_context(user_id, message)
        
        # Genera risposta intelligente
        response = skaila_brain.generate_intelligent_response(context)
        
        # Salva conversazione
        db_manager.execute('''
            INSERT INTO ai_conversations 
            (utente_id, message, response, detected_subject, sentiment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, message, response, 
              context.get('detected_subject', 'generale'),
              ','.join(context.get('sentiment', [])),
              datetime.now()))
        
        # Award XP per interazione AI
        gamification_system.award_xp(user_id, 'ai_question', 1.0, 
            "Domanda AI")
        
        return jsonify({
            'success': True,
            'response': response,
            'context': {
                'subject': context.get('detected_subject'),
                'level': context.get('livello'),
                'streak': context.get('streak')
            }
        })
    
    except Exception as e:
        print(f"❌ Errore AI chat: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/api/ai/quiz/get', methods=['POST'])
def get_quiz():
    """Ottieni quiz adattivo"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    data = request.get_json()
    subject = data.get('subject')
    difficulty = data.get('difficulty')  # Opzionale, se None è adattivo
    
    if not subject:
        return jsonify({'error': 'Materia non specificata'}), 400
    
    user_id = session['user_id']
    
    try:
        quiz = quiz_manager.get_adaptive_quiz(user_id, subject, difficulty)
        
        if not quiz:
            return jsonify({'error': 'Nessun quiz disponibile'}), 404
        
        # Salva TUTTO in sessione server-side (inclusa risposta corretta)
        session['current_quiz'] = {
            'id': quiz['id'],
            'correct_answer': quiz['correct_answer'],
            'subject': quiz['subject'],
            'topic': quiz['topic'],
            'difficulty': quiz['difficulty'],
            'xp_reward': quiz['xp_reward'],
            'explanation': quiz['explanation'],
            'start_time': datetime.now().isoformat()
        }
        
        # CRITICO: NON inviare MAI correct_answer e explanation al client!
        quiz_response = {
            'id': quiz['id'],
            'subject': quiz['subject'],
            'topic': quiz['topic'],
            'difficulty': quiz['difficulty'],
            'question': quiz['question'],
            'options': quiz['options'],
            'xp_reward': quiz['xp_reward']
        }
        
        return jsonify({
            'success': True,
            'quiz': quiz_response
        })
    
    except Exception as e:
        print(f"❌ Errore get quiz: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/api/ai/quiz/submit', methods=['POST'])
def submit_quiz():
    """Sottometti risposta quiz"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    if 'current_quiz' not in session:
        return jsonify({'error': 'Nessun quiz attivo'}), 400
    
    data = request.get_json()
    user_answer = data.get('answer', '').upper()
    
    if not user_answer or user_answer not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'Risposta non valida'}), 400
    
    user_id = session['user_id']
    quiz_data = session['current_quiz']
    
    try:
        # Calcola tempo impiegato
        start_time = datetime.fromisoformat(quiz_data['start_time'])
        time_taken = int((datetime.now() - start_time).total_seconds())
        
        # Processa risposta
        result = quiz_manager.submit_quiz_answer(
            user_id, 
            quiz_data['id'],
            quiz_data,
            user_answer,
            time_taken
        )
        
        # Pulisci sessione
        del session['current_quiz']
        
        return jsonify({
            'success': True,
            'is_correct': result['is_correct'],
            'correct_answer': quiz_data['correct_answer'],
            'explanation': quiz_data['explanation'],
            'xp_earned': result['xp_earned'],
            'speed_bonus': result.get('speed_bonus', False),
            'progress': result.get('progress', {})
        })
    
    except Exception as e:
        print(f"❌ Errore submit quiz: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/api/ai/progress/<subject>', methods=['GET'])
def get_subject_progress(subject):
    """Ottieni progressi per materia"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    user_id = session['user_id']
    
    try:
        progress = db_manager.query('''
            SELECT * FROM student_subject_progress 
            WHERE user_id = ? AND subject = ?
        ''', (user_id, subject), one=True)
        
        if not progress:
            return jsonify({
                'subject': subject,
                'total_quizzes': 0,
                'accuracy': 0,
                'total_xp': 0,
                'weak_topics': []
            })
        
        return jsonify({
            'subject': progress['subject'],
            'total_quizzes': progress['total_quizzes'],
            'correct_quizzes': progress['correct_quizzes'],
            'accuracy': round(progress['accuracy_percentage'], 1),
            'total_xp': progress['total_xp'],
            'weak_topics': progress['topics_weak'].split(',') if progress['topics_weak'] else [],
            'last_activity': progress['last_activity_date']
        })
    
    except Exception as e:
        print(f"❌ Errore progress: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/api/ai/leaderboard/<subject>', methods=['GET'])
def get_leaderboard(subject):
    """Classifica per materia"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    classe = request.args.get('classe')  # Opzionale
    limit = int(request.args.get('limit', 10))
    
    try:
        leaderboard = quiz_manager.get_subject_leaderboard(subject, classe, limit)
        
        # Trova posizione utente corrente
        user_id = session['user_id']
        user_rank = None
        for entry in leaderboard:
            if entry['user_id'] == user_id:
                user_rank = entry['rank']
                break
        
        return jsonify({
            'subject': subject,
            'leaderboard': leaderboard,
            'user_rank': user_rank
        })
    
    except Exception as e:
        print(f"❌ Errore leaderboard: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/api/ai/stats', methods=['GET'])
def get_ai_stats():
    """Statistiche generali AI studente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autenticato'}), 401
    
    user_id = session['user_id']
    
    try:
        # Total AI interactions
        total_ai = db_manager.query('''
            SELECT COUNT(*) as count FROM ai_conversations WHERE utente_id = ?
        ''', (user_id,), one=True)
        
        # Quiz stats globali
        quiz_stats = db_manager.query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                SUM(xp_earned) as total_xp
            FROM student_quiz_history WHERE user_id = ?
        ''', (user_id,), one=True)
        
        # Progress per materia
        subjects = db_manager.query('''
            SELECT subject, total_xp, accuracy_percentage, total_quizzes
            FROM student_subject_progress WHERE user_id = ?
            ORDER BY total_xp DESC
        ''', (user_id,))
        
        subjects_data = []
        for subj in subjects:
            subjects_data.append({
                'subject': subj['subject'],
                'xp': subj['total_xp'],
                'accuracy': round(subj['accuracy_percentage'], 1),
                'quizzes': subj['total_quizzes']
            })
        
        return jsonify({
            'total_ai_interactions': total_ai['count'] if total_ai else 0,
            'total_quizzes': quiz_stats['total'] if quiz_stats else 0,
            'correct_quizzes': quiz_stats['correct'] if quiz_stats else 0,
            'total_quiz_xp': quiz_stats['total_xp'] if quiz_stats else 0,
            'accuracy_overall': round((quiz_stats['correct'] / quiz_stats['total'] * 100), 1) if quiz_stats and quiz_stats['total'] > 0 else 0,
            'subjects': subjects_data
        })
    
    except Exception as e:
        print(f"❌ Errore stats: {e}")
        return jsonify({'error': str(e)}), 500


print("✅ SKAILA AI Routes registrate!")
