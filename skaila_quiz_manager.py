"""
SKAILA Quiz Manager - Sistema Gestione Quiz Intelligente
Generazione, selezione adattiva, tracking performance
"""

import sqlite3
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from database_manager import db_manager
from gamification import gamification_system

class QuizManager:
    """Gestione completa quiz SKAILA"""
    
    def __init__(self):
        self.difficulty_xp = {
            'facile': 30,
            'medio': 50,
            'difficile': 100
        }
    
    def get_adaptive_quiz(self, user_id: int, subject: str, force_difficulty: Optional[str] = None) -> Optional[Dict]:
        """Seleziona quiz adattivo basato su performance utente"""
        
        # Calcola difficoltà adattiva
        if force_difficulty:
            difficulty = force_difficulty
        else:
            difficulty = self._calculate_adaptive_difficulty(user_id, subject)
        
        # Trova argomenti deboli
        weak_topics = self._get_weak_topics(user_id, subject)
        
        # Query quiz appropriato
        if weak_topics:
            # Priorità a argomenti deboli (80% chance)
            if random.random() < 0.8:
                quiz = self._get_quiz_by_topic(subject, difficulty, weak_topics[0])
            else:
                quiz = self._get_random_quiz(subject, difficulty)
        else:
            quiz = self._get_random_quiz(subject, difficulty)
        
        if not quiz:
            return None
        
        return {
            'id': quiz['id'],
            'subject': quiz['subject'],
            'topic': quiz['topic'],
            'difficulty': quiz['difficulty'],
            'question': quiz['question'],
            'options': {
                'A': quiz['option_a'],
                'B': quiz['option_b'],
                'C': quiz['option_c'],
                'D': quiz['option_d']
            },
            'correct_answer': quiz['correct_answer'],
            'explanation': quiz['explanation'],
            'xp_reward': quiz['xp_reward']
        }
    
    def submit_quiz_answer(self, user_id: int, quiz_id: int, quiz_data: Dict, user_answer: str, time_taken: int) -> Dict:
        """Processa risposta quiz e aggiorna statistiche"""
        
        is_correct = (user_answer.upper() == quiz_data['correct_answer'].upper())
        
        # XP base
        xp_earned = quiz_data['xp_reward'] if is_correct else int(quiz_data['xp_reward'] * 0.2)
        
        # Bonus velocità (< 30 secondi = 1.2x)
        if time_taken < 30 and is_correct:
            xp_earned = int(xp_earned * 1.2)
        
        # Salva history
        db_manager.execute('''
            INSERT INTO student_quiz_history 
            (user_id, quiz_id, subject, topic, difficulty, user_answer, 
             correct_answer, is_correct, time_taken_seconds, xp_earned)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, quiz_id, quiz_data['subject'], quiz_data['topic'], 
              quiz_data['difficulty'], user_answer, quiz_data['correct_answer'],
              is_correct, time_taken, xp_earned))
        
        # Aggiorna progress materia
        self._update_subject_progress(user_id, quiz_data['subject'], quiz_data['topic'], is_correct, xp_earned)
        
        # Assegna XP gamification
        if is_correct:
            gamification_system.award_xp(user_id, 'ai_correct_answer', 1.0, 
                f"Quiz {quiz_data['subject']} corretto!")
        else:
            gamification_system.award_xp(user_id, 'ai_question', 0.5, 
                "Partecipazione quiz")
        
        # Check badge unlock
        self._check_quiz_badges(user_id, quiz_data['subject'], is_correct)
        
        # Aggiorna stats quiz
        db_manager.execute('''
            UPDATE quiz_bank 
            SET times_used = times_used + 1,
                success_rate = (
                    SELECT CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)
                    FROM student_quiz_history WHERE quiz_id = ?
                )
            WHERE id = ?
        ''', (quiz_id, quiz_id))
        
        result = {
            'is_correct': is_correct,
            'xp_earned': xp_earned,
            'explanation': quiz_data['explanation'] if not is_correct else None,
            'correct_answer': quiz_data['correct_answer'],
            'speed_bonus': time_taken < 30 and is_correct
        }
        
        # Info progresso
        progress = self._get_subject_progress_summary(user_id, quiz_data['subject'])
        result['progress'] = progress
        
        return result
    
    def _calculate_adaptive_difficulty(self, user_id: int, subject: str) -> str:
        """Calcola difficoltà adattiva basata su performance"""
        
        # Ultimi 10 quiz della materia
        recent_quizzes = db_manager.query('''
            SELECT is_correct, difficulty FROM student_quiz_history 
            WHERE user_id = ? AND subject = ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (user_id, subject))
        
        if not recent_quizzes or len(recent_quizzes) < 3:
            return 'facile'  # Inizia sempre facile
        
        # Calcola accuracy recente
        correct_count = sum(1 for q in recent_quizzes if q['is_correct'])
        accuracy = (correct_count / len(recent_quizzes)) * 100
        
        # Logica adattiva
        if accuracy >= 85:
            return 'difficile'
        elif accuracy >= 70:
            return 'medio'
        else:
            return 'facile'
    
    def _get_weak_topics(self, user_id: int, subject: str) -> List[str]:
        """Identifica argomenti deboli"""
        
        topic_stats = db_manager.query('''
            SELECT topic, 
                   COUNT(*) as total,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
            FROM student_quiz_history 
            WHERE user_id = ? AND subject = ?
            GROUP BY topic
            HAVING total >= 3
        ''', (user_id, subject))
        
        weak_topics = []
        for stat in topic_stats:
            accuracy = (stat['correct'] / stat['total']) * 100
            if accuracy < 70:
                weak_topics.append(stat['topic'])
        
        return weak_topics
    
    def _get_quiz_by_topic(self, subject: str, difficulty: str, topic: str) -> Optional[Dict]:
        """Trova quiz per argomento specifico"""
        
        quiz = db_manager.query('''
            SELECT * FROM quiz_bank 
            WHERE subject = ? AND difficulty = ? AND topic = ?
            AND approved = true
            ORDER BY RANDOM() LIMIT 1
        ''', (subject, difficulty, topic), one=True)
        
        return quiz
    
    def _get_random_quiz(self, subject: str, difficulty: str) -> Optional[Dict]:
        """Trova quiz casuale"""
        
        quiz = db_manager.query('''
            SELECT * FROM quiz_bank 
            WHERE subject = ? AND difficulty = ? AND approved = true
            ORDER BY RANDOM() LIMIT 1
        ''', (subject, difficulty), one=True)
        
        return quiz
    
    def _update_subject_progress(self, user_id: int, subject: str, topic: str, is_correct: bool, xp_earned: int):
        """Aggiorna progressi materia"""
        
        # Check se esiste
        existing = db_manager.query('''
            SELECT * FROM student_subject_progress 
            WHERE user_id = ? AND subject = ?
        ''', (user_id, subject), one=True)
        
        if existing:
            # Update
            new_total = existing['total_quizzes'] + 1
            new_correct = existing['correct_quizzes'] + (1 if is_correct else 0)
            new_accuracy = (new_correct / new_total) * 100
            new_xp = existing['total_xp'] + xp_earned
            
            # Gestisci topic deboli
            weak_topics = existing['topics_weak'].split(',') if existing['topics_weak'] else []
            if not is_correct and topic not in weak_topics:
                weak_topics.append(topic)
            elif is_correct and topic in weak_topics:
                # Rimuovi se migliora
                recent_topic_accuracy = self._get_topic_accuracy(user_id, subject, topic)
                if recent_topic_accuracy >= 70:
                    weak_topics.remove(topic)
            
            db_manager.execute('''
                UPDATE student_subject_progress 
                SET total_quizzes = ?, correct_quizzes = ?, 
                    accuracy_percentage = ?, total_xp = ?,
                    topics_weak = ?, last_activity_date = ?
                WHERE user_id = ? AND subject = ?
            ''', (new_total, new_correct, new_accuracy, new_xp,
                  ','.join(weak_topics), datetime.now(), user_id, subject))
        else:
            # Insert
            db_manager.execute('''
                INSERT INTO student_subject_progress 
                (user_id, subject, total_quizzes, correct_quizzes, 
                 accuracy_percentage, total_xp, topics_weak, last_activity_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, subject, 1, 1 if is_correct else 0,
                  100 if is_correct else 0, xp_earned,
                  topic if not is_correct else '', datetime.now()))
    
    def _get_topic_accuracy(self, user_id: int, subject: str, topic: str) -> float:
        """Calcola accuracy recente per topic"""
        
        stats = db_manager.query('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
            FROM student_quiz_history 
            WHERE user_id = ? AND subject = ? AND topic = ?
            AND timestamp >= datetime('now', '-7 days')
        ''', (user_id, subject, topic), one=True)
        
        if not stats or stats['total'] == 0:
            return 0
        
        return (stats['correct'] / stats['total']) * 100
    
    def _check_quiz_badges(self, user_id: int, subject: str, is_correct: bool):
        """Verifica unlock badge quiz"""
        
        if is_correct:
            # Consecutive correct quizzes
            consecutive = self._get_consecutive_correct(user_id)
            
            if consecutive >= 5:
                gamification_system.unlock_badge(user_id, 'quiz_streak_5')
            if consecutive >= 10:
                gamification_system.unlock_badge(user_id, 'quiz_master')
    
    def _get_consecutive_correct(self, user_id: int) -> int:
        """Conta quiz corretti consecutivi"""
        
        recent = db_manager.query('''
            SELECT is_correct FROM student_quiz_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT 10
        ''', (user_id,))
        
        consecutive = 0
        for quiz in recent:
            if quiz['is_correct']:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    def _get_subject_progress_summary(self, user_id: int, subject: str) -> Dict:
        """Riassunto progressi materia"""
        
        progress = db_manager.query('''
            SELECT * FROM student_subject_progress 
            WHERE user_id = ? AND subject = ?
        ''', (user_id, subject), one=True)
        
        if not progress:
            return {'accuracy': 0, 'total_quizzes': 0, 'xp': 0}
        
        return {
            'accuracy': round(progress['accuracy_percentage'], 1),
            'total_quizzes': progress['total_quizzes'],
            'xp': progress['total_xp'],
            'weak_topics': progress['topics_weak'].split(',') if progress['topics_weak'] else []
        }
    
    def get_subject_leaderboard(self, subject: str, classe: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Classifica per materia"""
        
        query = '''
            SELECT u.id, u.nome, u.cognome, ssp.total_xp, ssp.accuracy_percentage, ssp.total_quizzes
            FROM student_subject_progress ssp
            JOIN utenti u ON ssp.user_id = u.id
            WHERE ssp.subject = ?
        '''
        params = [subject]
        
        if classe:
            query += ' AND u.classe = ?'
            params.append(classe)
        
        query += ' ORDER BY ssp.total_xp DESC LIMIT ?'
        params.append(limit)
        
        results = db_manager.query(query, tuple(params))
        
        leaderboard = []
        for i, row in enumerate(results, 1):
            leaderboard.append({
                'rank': i,
                'user_id': row['id'],
                'nome': f"{row['nome']} {row['cognome']}",
                'xp': row['total_xp'],
                'accuracy': round(row['accuracy_percentage'], 1),
                'quizzes': row['total_quizzes']
            })
        
        return leaderboard
    
    def create_quiz(self, quiz_data: Dict) -> int:
        """Crea nuovo quiz"""
        
        cursor = db_manager.execute('''
            INSERT INTO quiz_bank 
            (subject, topic, difficulty, question, option_a, option_b, option_c, option_d,
             correct_answer, explanation, xp_reward, prerequisiti, tags, created_by, approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            quiz_data['subject'],
            quiz_data['topic'],
            quiz_data['difficulty'],
            quiz_data['question'],
            quiz_data['option_a'],
            quiz_data['option_b'],
            quiz_data['option_c'],
            quiz_data['option_d'],
            quiz_data['correct_answer'],
            quiz_data.get('explanation', ''),
            quiz_data.get('xp_reward', self.difficulty_xp[quiz_data['difficulty']]),
            quiz_data.get('prerequisiti', ''),
            quiz_data.get('tags', ''),
            quiz_data.get('created_by', 0),
            quiz_data.get('approved', True)
        ))
        
        return cursor.lastrowid if hasattr(cursor, 'lastrowid') else 0


# Inizializza sistema
quiz_manager = QuizManager()
print("✅ SKAILA Quiz Manager inizializzato!")
