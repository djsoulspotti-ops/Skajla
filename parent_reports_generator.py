"""
SKAILA Parent Reports Generator
Genera report automatici settimanali/mensili per genitori
"""

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from database_manager import db_manager
from registro_elettronico import registro
from ai_registro_intelligence import ai_registro

class ParentReportsGenerator:
    """Generatore report per genitori"""
    
    def generate_weekly_report(self, student_id: int) -> Dict:
        """Genera report settimanale"""
        
        # Get student info
        student = db_manager.query('''
            SELECT nome, cognome, classe FROM utenti WHERE id = ?
        ''', (student_id,), one=True)
        
        if not student:
            return {'error': 'Studente non trovato'}
        
        week_start = date.today() - timedelta(days=7)
        
        # Attendance this week
        attendance_week = db_manager.query('''
            SELECT status, date FROM registro_presenze
            WHERE student_id = ? AND date >= ?
            ORDER BY date DESC
        ''', (student_id, week_start))
        
        # Grades this week
        grades_week = db_manager.query('''
            SELECT rv.*, u.nome as teacher_name, u.cognome as teacher_surname
            FROM registro_voti rv
            JOIN utenti u ON rv.teacher_id = u.id
            WHERE rv.student_id = ? AND rv.date >= ?
            ORDER BY rv.date DESC
        ''', (student_id, week_start))
        
        # Disciplinary notes this week
        notes_week = db_manager.query('''
            SELECT * FROM registro_note_disciplinari
            WHERE student_id = ? AND date >= ?
        ''', (student_id, week_start))
        
        # Homework/Lessons this week
        lessons_week = db_manager.query('''
            SELECT rcl.* FROM registro_calendario_lezioni rcl
            JOIN utenti u ON ? = ?
            WHERE rcl.class = ? AND rcl.lesson_date >= ? AND rcl.homework IS NOT NULL
            ORDER BY rcl.lesson_date DESC
        ''', (student_id, student_id, student['classe'], week_start))
        
        # Overall averages
        averages = registro.get_subject_averages(student_id)
        
        # AI insights
        risk = ai_registro.analyze_student_risk(student_id)
        
        report = {
            'student': f"{student['nome']} {student['cognome']}",
            'class': student['classe'],
            'report_period': f"{week_start} - {date.today()}",
            'report_type': 'settimanale',
            
            'attendance_summary': {
                'total_days': len(attendance_week),
                'present': sum(1 for a in attendance_week if a['status'] == 'presente'),
                'absent': sum(1 for a in attendance_week if a['status'] == 'assente'),
                'late': sum(1 for a in attendance_week if a['status'] == 'ritardo'),
                'details': [
                    {'date': str(a['date']), 'status': a['status']} 
                    for a in attendance_week
                ]
            },
            
            'grades_summary': {
                'new_grades_count': len(grades_week),
                'new_grades': [
                    {
                        'subject': g['subject'],
                        'voto': float(g['voto']),
                        'tipo': g['tipo'],
                        'description': g['description'],
                        'date': str(g['date']),
                        'teacher': f"{g['teacher_name']} {g['teacher_surname']}"
                    }
                    for g in grades_week
                ],
                'current_averages': [
                    {'subject': a['subject'], 'media': a['average'], 'status': a['status']}
                    for a in averages
                ]
            },
            
            'behavior_summary': {
                'disciplinary_notes': len(notes_week),
                'notes_details': [
                    {
                        'type': n['note_type'],
                        'severity': n['severity'],
                        'description': n['description'],
                        'date': str(n['date'])
                    }
                    for n in notes_week
                ] if notes_week else []
            },
            
            'homework_this_week': [
                {
                    'subject': l['subject'],
                    'date': str(l['lesson_date']),
                    'topic': l['topic'],
                    'homework': l['homework']
                }
                for l in lessons_week
            ],
            
            'ai_insights': {
                'risk_level': risk['risk_level'],
                'main_strengths': self._identify_strengths(averages),
                'areas_for_improvement': [rf['description'] for rf in risk['risk_factors'][:3]],
                'recommendations': risk['suggested_actions']
            },
            
            'parent_action_items': self._generate_parent_actions(risk, attendance_week, grades_week)
        }
        
        return report
    
    def generate_monthly_report(self, student_id: int) -> Dict:
        """Genera report mensile"""
        
        # Get student info
        student = db_manager.query('''
            SELECT nome, cognome, classe FROM utenti WHERE id = ?
        ''', (student_id,), one=True)
        
        if not student:
            return {'error': 'Studente non trovato'}
        
        month_start = date.today() - timedelta(days=30)
        
        # Full report
        full_report = registro.get_student_report(student_id, months=1)
        
        # Performance trends
        trend_analysis = self._analyze_monthly_trends(student_id, month_start)
        
        # AI comprehensive analysis
        risk = ai_registro.analyze_student_risk(student_id)
        anomalies = ai_registro.detect_performance_anomalies(student_id)
        intervention = ai_registro.generate_personalized_intervention(student_id)
        
        report = {
            'student': f"{student['nome']} {student['cognome']}",
            'class': student['classe'],
            'report_period': f"{month_start} - {date.today()}",
            'report_type': 'mensile',
            
            'executive_summary': {
                'overall_status': full_report['overall_status'],
                'attendance_rate': full_report['attendance']['percentuale_presenza'],
                'avg_grade': self._calculate_overall_average(full_report['subject_averages']),
                'behavior_score': self._calculate_behavior_score(full_report['disciplinary_notes']),
                'improvement_trend': trend_analysis['overall_trend']
            },
            
            'detailed_attendance': full_report['attendance'],
            
            'academic_performance': {
                'subject_averages': full_report['subject_averages'],
                'best_subjects': [a['subject'] for a in full_report['subject_averages'][:3]],
                'subjects_needing_attention': [
                    a['subject'] for a in full_report['subject_averages'] 
                    if a['average'] < 6
                ]
            },
            
            'behavior_analysis': {
                'total_notes': full_report['disciplinary_notes'],
                'unjustified_absences': full_report['unjustified_absences'],
                'behavior_status': 'positivo' if full_report['disciplinary_notes'] == 0 else 'da migliorare'
            },
            
            'trends_and_patterns': trend_analysis,
            
            'ai_insights': {
                'risk_assessment': {
                    'level': risk['risk_level'],
                    'score': risk['risk_score'],
                    'factors': risk['risk_factors']
                },
                'anomalies_detected': anomalies,
                'intervention_plan': intervention['intervention_plan'] if intervention else [],
                'success_indicators': intervention['success_indicators'] if intervention else []
            },
            
            'recommendations_for_parents': self._generate_parent_recommendations(
                risk, full_report, trend_analysis
            ),
            
            'next_steps': {
                'parent_actions': self._generate_parent_actions(risk, [], []),
                'school_actions': intervention['intervention_plan'][:3] if intervention else [],
                'follow_up_date': intervention.get('follow_up_date', (date.today() + timedelta(weeks=2)).isoformat())
            }
        }
        
        return report
    
    def generate_parent_notification(self, student_id: int, event_type: str, data: Dict) -> Dict:
        """Genera notifica immediata per genitori"""
        
        student = db_manager.query('''
            SELECT nome, cognome FROM utenti WHERE id = ?
        ''', (student_id,), one=True)
        
        notifications = {
            'new_grade': f"Nuovo voto: {data['subject']} - {data['voto']} ({data.get('description', '')})",
            'absence': f"Assenza registrata il {data['date']}. Ricorda di giustificare.",
            'disciplinary_note': f"Nota disciplinare: {data.get('description', '')} (Gravità: {data.get('severity', 'media')})",
            'low_grade': f"Attenzione: voto basso in {data['subject']} ({data['voto']}). Suggerito supporto.",
            'multiple_absences': f"Rilevate {data['count']} assenze nelle ultime 2 settimane. Verifica situazione.",
            'excellent_performance': f"Ottimo risultato in {data['subject']}: {data['voto']}! Complimenti!",
            'improvement_needed': f"Il rendimento in {data['subject']} necessita attenzione. Contattare il docente."
        }
        
        message = notifications.get(event_type, f"Aggiornamento per {student['nome']} {student['cognome']}")
        
        return {
            'student_id': student_id,
            'student_name': f"{student['nome']} {student['cognome']}",
            'event_type': event_type,
            'message': message,
            'priority': self._determine_priority(event_type),
            'timestamp': datetime.now().isoformat(),
            'requires_action': event_type in ['absence', 'disciplinary_note', 'multiple_absences', 'improvement_needed']
        }
    
    def _analyze_monthly_trends(self, student_id: int, month_start: date) -> Dict:
        """Analizza trend mensili"""
        
        # Grade trends
        grades = db_manager.query('''
            SELECT subject, voto, date FROM registro_voti
            WHERE student_id = ? AND date >= ?
            ORDER BY date ASC
        ''', (student_id, month_start))
        
        # Group by subject
        subject_trends = {}
        for g in grades:
            subj = g['subject']
            if subj not in subject_trends:
                subject_trends[subj] = []
            subject_trends[subj].append(float(g['voto']))
        
        # Calculate trends
        trends = {}
        for subj, voti in subject_trends.items():
            if len(voti) >= 3:
                first_half_avg = sum(voti[:len(voti)//2]) / (len(voti)//2)
                second_half_avg = sum(voti[len(voti)//2:]) / (len(voti) - len(voti)//2)
                
                if second_half_avg > first_half_avg + 0.5:
                    trends[subj] = 'miglioramento'
                elif second_half_avg < first_half_avg - 0.5:
                    trends[subj] = 'calo'
                else:
                    trends[subj] = 'stabile'
        
        # Overall trend
        improving = sum(1 for t in trends.values() if t == 'miglioramento')
        declining = sum(1 for t in trends.values() if t == 'calo')
        
        if improving > declining:
            overall = 'miglioramento'
        elif declining > improving:
            overall = 'calo'
        else:
            overall = 'stabile'
        
        return {
            'overall_trend': overall,
            'subject_trends': trends,
            'improving_subjects': [s for s, t in trends.items() if t == 'miglioramento'],
            'declining_subjects': [s for s, t in trends.items() if t == 'calo']
        }
    
    def _identify_strengths(self, averages: List[Dict]) -> List[str]:
        """Identifica punti di forza"""
        
        strengths = []
        
        excellent = [a for a in averages if a['average'] >= 8]
        for subj in excellent[:3]:  # Top 3
            strengths.append(f"Eccellente in {subj['subject']} (media {subj['average']})")
        
        if not strengths:
            good = [a for a in averages if a['average'] >= 7]
            for subj in good[:2]:
                strengths.append(f"Buoni risultati in {subj['subject']}")
        
        return strengths if strengths else ["Mantiene impegno costante"]
    
    def _generate_parent_actions(self, risk: Dict, attendance: List, grades: List) -> List[str]:
        """Genera azioni per genitori"""
        
        actions = []
        
        if risk['risk_level'] in ['critico', 'alto']:
            actions.append("🔴 URGENTE: Richiesto colloquio con coordinatore classe")
        
        for factor in risk['risk_factors']:
            if factor['category'] == 'presenze':
                actions.append("📅 Monitorare quotidianamente la frequenza scolastica")
            elif factor['category'] == 'rendimento':
                actions.append("📚 Organizzare sessioni studio casa o tutoraggio privato")
            elif factor['category'] == 'disciplina':
                actions.append("👨‍👩‍👦 Discutere comportamento scolastico e aspettative")
        
        if not actions:
            actions.append("✅ Continuare a supportare con l'attuale approccio")
        
        return actions
    
    def _generate_parent_recommendations(self, risk: Dict, report: Dict, trends: Dict) -> List[str]:
        """Genera raccomandazioni complete per genitori"""
        
        recommendations = []
        
        # Academic
        if report['subject_averages']:
            failing = [a for a in report['subject_averages'] if a['average'] < 6]
            if failing:
                subjects_str = ', '.join([s['subject'] for s in failing[:2]])
                recommendations.append(
                    f"📚 Priorità: supporto in {subjects_str}. "
                    f"Considerare tutoraggio o materiali integrativi."
                )
        
        # Attendance
        if report['attendance']['percentuale_presenza'] < 90:
            recommendations.append(
                "🏥 Frequenza insufficiente. Verificare eventuali problemi di salute "
                "o disagio scolastico. Contattare il medico se necessario."
            )
        
        # Behavior
        if report['disciplinary_notes'] > 2:
            recommendations.append(
                "👨‍👩‍👦 Comportamento da migliorare. Dialogo aperto a casa e "
                "collaborazione con la scuola per stabilire regole chiare."
            )
        
        # Trends
        if trends['overall_trend'] == 'calo':
            recommendations.append(
                "📉 Rilevato calo generale. Indagare possibili cause: "
                "stress, problemi personali, metodo studio. Supporto psicologico se necessario."
            )
        elif trends['overall_trend'] == 'miglioramento':
            recommendations.append(
                "🎉 Trend positivo! Rinforzare le strategie attuali e celebrare i successi."
            )
        
        # Risk-based
        if risk['risk_level'] == 'critico':
            recommendations.append(
                "🚨 SITUAZIONE CRITICA: intervento immediato richiesto. "
                "Fissare colloquio urgente con coordinatore e psicologo scolastico."
            )
        
        if not recommendations:
            recommendations.append(
                "✨ Andamento regolare. Continuare a monitorare e supportare "
                "con interesse e dialogo costante."
            )
        
        return recommendations
    
    def _calculate_overall_average(self, subject_averages: List[Dict]) -> float:
        """Calcola media generale"""
        if not subject_averages:
            return 0.0
        return round(sum(a['average'] for a in subject_averages) / len(subject_averages), 2)
    
    def _calculate_behavior_score(self, notes_count: int) -> int:
        """Calcola punteggio comportamento (1-10)"""
        if notes_count == 0:
            return 10
        elif notes_count == 1:
            return 8
        elif notes_count <= 3:
            return 6
        else:
            return 4
    
    def _determine_priority(self, event_type: str) -> str:
        """Determina priorità notifica"""
        high_priority = ['disciplinary_note', 'multiple_absences', 'improvement_needed']
        medium_priority = ['low_grade', 'absence']
        
        if event_type in high_priority:
            return 'alta'
        elif event_type in medium_priority:
            return 'media'
        else:
            return 'bassa'


# Initialize
parent_reports = ParentReportsGenerator()
print("✅ Parent Reports Generator inizializzato!")
