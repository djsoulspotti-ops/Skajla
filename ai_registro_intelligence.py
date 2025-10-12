"""
SKAILA AI Registro Intelligence
AI analizza registro e suggerisce interventi personalizzati
"""

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from database_manager import db_manager
from registro_elettronico import registro

class AIRegistroIntelligence:
    """AI Intelligence per Registro Elettronico"""
    
    def analyze_student_risk(self, student_id: int) -> Dict:
        """Analisi rischio studente con AI"""
        
        # Get comprehensive data
        report = registro.get_student_report(student_id, months=3)
        attendance = report['attendance']
        averages = report['subject_averages']
        
        # Calculate risk score (0-100, higher = more risk)
        risk_score = 0
        risk_factors = []
        
        # Attendance risk
        if attendance['percentuale_presenza'] < 75:
            risk_score += 30
            risk_factors.append({
                'category': 'presenze',
                'severity': 'alta',
                'description': f"Presenza critica: {attendance['percentuale_presenza']}%",
                'recommendation': 'Contattare famiglia urgentemente'
            })
        elif attendance['percentuale_presenza'] < 85:
            risk_score += 15
            risk_factors.append({
                'category': 'presenze',
                'severity': 'media',
                'description': f"Presenza bassa: {attendance['percentuale_presenza']}%",
                'recommendation': 'Monitorare assenze e comunicare con famiglia'
            })
        
        # Unjustified absences
        if attendance['assenze_non_giustificate'] > 5:
            risk_score += 20
            risk_factors.append({
                'category': 'assenze',
                'severity': 'alta',
                'description': f"{attendance['assenze_non_giustificate']} assenze non giustificate",
                'recommendation': 'Richiedere giustificazioni immediate'
            })
        
        # Academic performance
        failing_subjects = [a for a in averages if a['average'] < 6]
        if len(failing_subjects) > 2:
            risk_score += 25
            subjects_str = ', '.join([s['subject'] for s in failing_subjects[:3]])
            risk_factors.append({
                'category': 'rendimento',
                'severity': 'alta',
                'description': f"{len(failing_subjects)} materie insufficienti: {subjects_str}",
                'recommendation': 'Piano recupero personalizzato urgente'
            })
        elif len(failing_subjects) > 0:
            risk_score += 10
            risk_factors.append({
                'category': 'rendimento',
                'severity': 'media',
                'description': f"Insufficienza in {failing_subjects[0]['subject']}",
                'recommendation': 'Supporto didattico mirato'
            })
        
        # Disciplinary
        if report['disciplinary_notes'] > 3:
            risk_score += 15
            risk_factors.append({
                'category': 'disciplina',
                'severity': 'media',
                'description': f"{report['disciplinary_notes']} note disciplinari",
                'recommendation': 'Colloquio con coordinatore e famiglia'
            })
        
        # Performance trend
        trend = self._analyze_performance_trend(student_id)
        if trend == 'declining':
            risk_score += 20
            risk_factors.append({
                'category': 'trend',
                'severity': 'alta',
                'description': 'Rendimento in calo significativo',
                'recommendation': 'Intervento immediato: analisi cause e supporto'
            })
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = 'critico'
            priority = 'urgente'
        elif risk_score >= 30:
            risk_level = 'alto'
            priority = 'alta'
        elif risk_score >= 15:
            risk_level = 'medio'
            priority = 'media'
        else:
            risk_level = 'basso'
            priority = 'normale'
        
        return {
            'student_id': student_id,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'priority': priority,
            'risk_factors': risk_factors,
            'suggested_actions': self._generate_action_plan(risk_factors),
            'analysis_date': datetime.now().isoformat()
        }
    
    def identify_students_at_risk(self, class_name: str, min_risk_score: int = 30) -> List[Dict]:
        """Identifica tutti gli studenti a rischio in una classe"""
        
        # Get all students in class
        students = db_manager.query('''
            SELECT id, nome, cognome FROM utenti 
            WHERE classe = ? AND ruolo = 'studente'
        ''', (class_name,))
        
        at_risk = []
        
        for student in students:
            analysis = self.analyze_student_risk(student['id'])
            
            if analysis['risk_score'] >= min_risk_score:
                at_risk.append({
                    'student_id': student['id'],
                    'nome': f"{student['nome']} {student['cognome']}",
                    'risk_score': analysis['risk_score'],
                    'risk_level': analysis['risk_level'],
                    'priority': analysis['priority'],
                    'main_issues': [rf['category'] for rf in analysis['risk_factors'][:3]]
                })
        
        # Sort by risk score descending
        at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return at_risk
    
    def detect_performance_anomalies(self, student_id: int) -> List[Dict]:
        """Rileva anomalie nel rendimento"""
        
        anomalies = []
        
        # Sudden grade drop
        grades = db_manager.query('''
            SELECT subject, voto, date FROM registro_voti
            WHERE student_id = ?
            ORDER BY date DESC LIMIT 20
        ''', (student_id,))
        
        # Group by subject
        by_subject = {}
        for g in grades:
            subj = g['subject']
            if subj not in by_subject:
                by_subject[subj] = []
            by_subject[subj].append(float(g['voto']))
        
        # Check for drops
        for subject, voti in by_subject.items():
            if len(voti) >= 3:
                recent_avg = sum(voti[:2]) / 2
                older_avg = sum(voti[2:]) / len(voti[2:])
                
                if recent_avg < older_avg - 1.5:  # Drop > 1.5 points
                    anomalies.append({
                        'type': 'calo_voti',
                        'subject': subject,
                        'description': f"Calo significativo in {subject}: da {older_avg:.1f} a {recent_avg:.1f}",
                        'severity': 'alta' if (older_avg - recent_avg) > 2.5 else 'media'
                    })
        
        # Absence pattern changes
        recent_absences = db_manager.query('''
            SELECT COUNT(*) as count FROM registro_presenze
            WHERE student_id = ? AND status = 'assente' 
            AND date >= ?
        ''', (student_id, date.today() - timedelta(days=30)), one=True)
        
        older_absences = db_manager.query('''
            SELECT COUNT(*) as count FROM registro_presenze
            WHERE student_id = ? AND status = 'assente'
            AND date BETWEEN ? AND ?
        ''', (student_id, date.today() - timedelta(days=90), date.today() - timedelta(days=30)), one=True)
        
        if recent_absences and older_absences:
            if recent_absences['count'] > older_absences['count'] * 2:
                anomalies.append({
                    'type': 'aumento_assenze',
                    'description': f"Assenze raddoppiate: {older_absences['count']} → {recent_absences['count']} (ultimo mese)",
                    'severity': 'alta'
                })
        
        return anomalies
    
    def generate_personalized_intervention(self, student_id: int) -> Dict:
        """Genera piano intervento personalizzato"""
        
        risk = self.analyze_student_risk(student_id)
        anomalies = self.detect_performance_anomalies(student_id)
        report = registro.get_student_report(student_id, months=3)
        
        interventions = []
        
        # Based on risk factors
        for factor in risk['risk_factors']:
            if factor['category'] == 'presenze':
                interventions.append({
                    'area': 'Presenze',
                    'action': 'Monitoraggio quotidiano',
                    'who': 'Coordinatore + Famiglia',
                    'timeline': 'Immediato',
                    'goal': 'Riportare presenza > 90%'
                })
            
            elif factor['category'] == 'rendimento':
                failing = [a for a in report['subject_averages'] if a['average'] < 6]
                for subj in failing:
                    interventions.append({
                        'area': f"Recupero {subj['subject']}",
                        'action': 'Tutoraggio peer + materiali extra',
                        'who': 'Docente materia + studente tutor',
                        'timeline': '2 settimane',
                        'goal': f"Portare media a 6+ (attuale: {subj['average']})"
                    })
            
            elif factor['category'] == 'disciplina':
                interventions.append({
                    'area': 'Comportamento',
                    'action': 'Colloquio individuale + patto educativo',
                    'who': 'Coordinatore + Psicologo scolastico',
                    'timeline': '1 settimana',
                    'goal': 'Zero note per 1 mese'
                })
        
        # Based on anomalies
        for anomaly in anomalies:
            if anomaly['type'] == 'calo_voti':
                interventions.append({
                    'area': f"Analisi calo {anomaly['subject']}",
                    'action': 'Colloquio individuale per identificare cause',
                    'who': 'Docente + Coordinatore',
                    'timeline': '3 giorni',
                    'goal': 'Identificare blocchi e risolverli'
                })
        
        return {
            'student_id': student_id,
            'risk_level': risk['risk_level'],
            'intervention_plan': interventions,
            'follow_up_date': (date.today() + timedelta(weeks=2)).isoformat(),
            'success_indicators': self._define_success_indicators(risk, report)
        }
    
    def _analyze_performance_trend(self, student_id: int) -> str:
        """Analizza trend performance"""
        
        # Get grades from last 3 months
        grades = db_manager.query('''
            SELECT voto, date FROM registro_voti
            WHERE student_id = ? AND date >= ?
            ORDER BY date ASC
        ''', (student_id, date.today() - timedelta(days=90)))
        
        if len(grades) < 6:
            return 'insufficient_data'
        
        # Split into periods
        mid = len(grades) // 2
        recent = grades[mid:]
        older = grades[:mid]
        
        recent_avg = sum(float(g['voto']) for g in recent) / len(recent)
        older_avg = sum(float(g['voto']) for g in older) / len(older)
        
        diff = recent_avg - older_avg
        
        if diff > 0.5:
            return 'improving'
        elif diff < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_action_plan(self, risk_factors: List[Dict]) -> List[str]:
        """Genera piano azioni"""
        
        actions = []
        
        categories = {rf['category'] for rf in risk_factors}
        
        if 'presenze' in categories:
            actions.append("📞 Contatto immediato famiglia per gestione assenze")
        
        if 'rendimento' in categories:
            actions.append("📚 Attivazione piano recupero con tutoraggio")
        
        if 'disciplina' in categories:
            actions.append("👥 Colloquio studente-coordinatore-famiglia")
        
        if 'trend' in categories:
            actions.append("🔍 Analisi approfondita cause calo rendimento")
        
        if not actions:
            actions.append("✅ Monitoraggio standard - situazione sotto controllo")
        
        return actions
    
    def _define_success_indicators(self, risk: Dict, report: Dict) -> List[str]:
        """Definisci indicatori successo"""
        
        indicators = []
        
        # Attendance target
        current_attendance = report['attendance']['percentuale_presenza']
        if current_attendance < 85:
            target = min(current_attendance + 10, 95)
            indicators.append(f"Presenza ≥ {target}%")
        
        # Academic targets
        failing = [a for a in report['subject_averages'] if a['average'] < 6]
        if failing:
            indicators.append(f"Almeno 1 insufficienza recuperata")
        
        # Discipline
        if report['disciplinary_notes'] > 0:
            indicators.append("Zero note disciplinari per 30 giorni")
        
        # Justifications
        if report['unjustified_absences'] > 0:
            indicators.append("Tutte assenze giustificate")
        
        return indicators
    
    def generate_class_health_report(self, class_name: str) -> Dict:
        """Report salute classe"""
        
        students = db_manager.query('''
            SELECT id FROM utenti WHERE classe = ? AND ruolo = 'studente'
        ''', (class_name,))
        
        total = len(students)
        at_risk = self.identify_students_at_risk(class_name, min_risk_score=30)
        critical = [s for s in at_risk if s['risk_level'] == 'critico']
        
        # Average attendance
        avg_attendance = db_manager.query('''
            SELECT AVG(
                CASE WHEN rp.status = 'presente' THEN 100.0 ELSE 0 END
            ) as avg_presence
            FROM registro_presenze rp
            JOIN utenti u ON rp.student_id = u.id
            WHERE u.classe = ? AND rp.date >= ?
        ''', (class_name, date.today() - timedelta(days=30)), one=True)
        
        # Average grades per subject
        avg_grades = db_manager.query('''
            SELECT rv.subject, AVG(rv.voto) as avg_voto
            FROM registro_voti rv
            JOIN utenti u ON rv.student_id = u.id
            WHERE u.classe = ? AND rv.date >= ?
            GROUP BY rv.subject
        ''', (class_name, date.today() - timedelta(days=30)))
        
        return {
            'class': class_name,
            'total_students': total,
            'students_at_risk': len(at_risk),
            'critical_students': len(critical),
            'class_health_score': self._calculate_class_health(total, len(at_risk), len(critical)),
            'avg_attendance': round(avg_attendance['avg_presence'], 1) if avg_attendance else 0,
            'subject_averages': [
                {'subject': g['subject'], 'average': round(float(g['avg_voto']), 2)}
                for g in avg_grades
            ],
            'top_concerns': self._identify_class_concerns(class_name, at_risk)
        }
    
    def _calculate_class_health(self, total: int, at_risk: int, critical: int) -> int:
        """Calcola health score classe (0-100)"""
        
        if total == 0:
            return 100
        
        risk_percentage = (at_risk / total) * 100
        critical_percentage = (critical / total) * 100
        
        # Start at 100, deduct based on risk
        score = 100
        score -= risk_percentage * 0.5  # -0.5 per ogni % at risk
        score -= critical_percentage * 2  # -2 per ogni % critical
        
        return max(0, int(score))
    
    def _identify_class_concerns(self, class_name: str, at_risk: List[Dict]) -> List[str]:
        """Identifica preoccupazioni principali classe"""
        
        concerns = []
        
        # Count issue types
        issue_counts = {}
        for student in at_risk:
            for issue in student['main_issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Report most common
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            concerns.append(f"{count} studenti con problemi di {issue}")
        
        return concerns if concerns else ["Nessuna preoccupazione significativa"]


# Initialize
ai_registro = AIRegistroIntelligence()
print("✅ AI Registro Intelligence inizializzato!")
