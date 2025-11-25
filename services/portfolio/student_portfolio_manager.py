"""
Student Portfolio Manager
Generates comprehensive "Candidate Cards" for SKAILA Connect
Aggregates: Grades, Badges, Skills, Projects, Gamification Data
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from services.database.database_manager import DatabaseManager
from shared.error_handling import get_logger, handle_errors

logger = get_logger(__name__)


class StudentPortfolioManager:
    """Manages student portfolio generation and 'Candidate Card' creation"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def generate_candidate_card(self, user_id: int, include_private: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive 'Candidate Card' for a student
        
        Args:
            user_id: Student user ID
            include_private: Include private information (grades, personal data)
        
        Returns:
            Dict containing structured candidate data ready for companies
        """
        logger.info(
            event_type='candidate_card_generation_started',
            domain='portfolio',
            user_id=user_id,
            include_private=include_private
        )
        
        student_info = self._get_student_basic_info(user_id)
        if not student_info:
            logger.warning(
                event_type='student_not_found',
                domain='portfolio',
                user_id=user_id
            )
            return {}
        
        candidate_card = {
            'candidate_id': user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'personal_info': {
                'name': f"{student_info.get('nome', '')} {student_info.get('cognome', '')}".strip(),
                'school': student_info.get('scuola_nome', 'N/A'),
                'class': student_info.get('classe', 'N/A'),
                'avatar': student_info.get('avatar') or '/static/default_avatar.png'
            },
            'academic_performance': self._get_academic_performance(user_id) if include_private else {},
            'badges_certifications': self._get_badges_certifications(user_id),
            'skills': self._get_student_skills(user_id),
            'projects': self._get_student_projects(user_id),
            'gamification_stats': self._get_gamification_stats(user_id),
            'soft_skills': self._get_soft_skills(user_id),
            'languages': self._get_languages(user_id),
            'portfolio_url': f'/student/portfolio/{user_id}',
            'profile_completeness': 0
        }
        
        candidate_card['profile_completeness'] = self._calculate_completeness(candidate_card)
        
        logger.info(
            event_type='candidate_card_generated',
            domain='portfolio',
            user_id=user_id,
            completeness=candidate_card['profile_completeness']
        )
        
        return candidate_card
    
    def _get_student_basic_info(self, user_id: int) -> Optional[Dict]:
        """Get basic student information from utenti table"""
        return self.db_manager.query('''
            SELECT 
                u.id,
                u.nome,
                u.cognome,
                u.email,
                u.classe,
                u.avatar,
                s.nome as scuola_nome
            FROM utenti u
            LEFT JOIN scuole s ON u.scuola_id = s.id
            WHERE u.id = %s AND u.ruolo = 'studente'
        ''', (user_id,), one=True)
    
    def _get_academic_performance(self, user_id: int) -> Dict:
        """Get verified grades and academic performance"""
        grades = self.db_manager.query('''
            SELECT 
                materia,
                voto,
                data_valutazione,
                tipo_valutazione
            FROM registro_voti
            WHERE user_id = %s
            ORDER BY data_valutazione DESC
            LIMIT 20
        ''', (user_id,)) or []
        
        if not grades:
            return {'average_gpa': 'N/A', 'recent_grades': [], 'top_subjects': []}
        
        numeric_grades = [float(g['voto']) for g in grades if g.get('voto') and str(g['voto']).replace('.', '').isdigit()]
        avg_gpa = round(sum(numeric_grades) / len(numeric_grades), 2) if numeric_grades else 'N/A'
        
        subject_averages = {}
        for grade in grades:
            subject = grade.get('materia', 'Unknown')
            if grade.get('voto') and str(grade['voto']).replace('.', '').isdigit():
                if subject not in subject_averages:
                    subject_averages[subject] = []
                subject_averages[subject].append(float(grade['voto']))
        
        top_subjects = [
            {'subject': subj, 'average': round(sum(voti) / len(voti), 2)}
            for subj, voti in subject_averages.items()
        ]
        top_subjects.sort(key=lambda x: x['average'], reverse=True)
        
        return {
            'average_gpa': avg_gpa,
            'recent_grades': [
                {
                    'subject': g.get('materia'),
                    'grade': g.get('voto'),
                    'date': g.get('data_valutazione').isoformat() if g.get('data_valutazione') else None,
                    'type': g.get('tipo_valutazione')
                }
                for g in grades[:5]
            ],
            'top_subjects': top_subjects[:3]
        }
    
    def _get_badges_certifications(self, user_id: int) -> List[Dict]:
        """Get user badges and certifications"""
        badges = self.db_manager.query('''
            SELECT 
                badge_id,
                badge_name,
                earned_at,
                description
            FROM user_badges
            WHERE user_id = %s
            ORDER BY earned_at DESC
        ''', (user_id,)) or []
        
        return [
            {
                'id': b.get('badge_id'),
                'name': b.get('badge_name'),
                'earned_at': b.get('earned_at').isoformat() if b.get('earned_at') else None,
                'description': b.get('description')
            }
            for b in badges
        ]
    
    def _get_student_skills(self, user_id: int) -> List[Dict]:
        """Get student skills with proficiency levels"""
        skills = self.db_manager.query('''
            SELECT 
                skill_name,
                skill_category,
                proficiency_level,
                verified,
                verified_by
            FROM student_skills
            WHERE user_id = %s
            ORDER BY 
                CASE proficiency_level
                    WHEN 'expert' THEN 1
                    WHEN 'advanced' THEN 2
                    WHEN 'intermediate' THEN 3
                    ELSE 4
                END,
                verified DESC
        ''', (user_id,)) or []
        
        return [
            {
                'name': s.get('skill_name'),
                'category': s.get('skill_category'),
                'level': s.get('proficiency_level'),
                'verified': s.get('verified', False),
                'verified_by': s.get('verified_by')
            }
            for s in skills
        ]
    
    def _get_student_projects(self, user_id: int) -> List[Dict]:
        """Get student projects and achievements"""
        projects = self.db_manager.query('''
            SELECT 
                title,
                description,
                project_type,
                technologies,
                start_date,
                end_date,
                is_ongoing,
                achievements,
                project_url
            FROM student_projects
            WHERE user_id = %s
            ORDER BY 
                is_ongoing DESC,
                COALESCE(end_date, CURRENT_DATE) DESC
        ''', (user_id,)) or []
        
        return [
            {
                'title': p.get('title'),
                'description': p.get('description'),
                'type': p.get('project_type'),
                'technologies': p.get('technologies', []),
                'duration': self._format_project_duration(p.get('start_date'), p.get('end_date'), p.get('is_ongoing')),
                'achievements': p.get('achievements'),
                'url': p.get('project_url')
            }
            for p in projects
        ]
    
    def _get_gamification_stats(self, user_id: int) -> Dict:
        """Get gamification stats (XP, level, badges count)"""
        stats = self.db_manager.query('''
            SELECT 
                total_xp,
                current_level,
                badge_count,
                streak_days
            FROM user_gamification
            WHERE user_id = %s
        ''', (user_id,), one=True)
        
        if not stats:
            return {'level': 1, 'xp': 0, 'badges': 0, 'streak': 0}
        
        return {
            'level': stats.get('current_level', 1),
            'xp': stats.get('total_xp', 0),
            'badges': stats.get('badge_count', 0),
            'streak': stats.get('streak_days', 0)
        }
    
    def _get_soft_skills(self, user_id: int) -> List[str]:
        """Get soft skills from student_portfolios"""
        portfolio = self.db_manager.query('''
            SELECT soft_skills
            FROM student_portfolios
            WHERE user_id = %s
        ''', (user_id,), one=True)
        
        if not portfolio or not portfolio.get('soft_skills'):
            return ['Communication', 'Teamwork', 'Problem Solving']
        
        soft_skills = portfolio.get('soft_skills')
        if isinstance(soft_skills, str):
            try:
                soft_skills = json.loads(soft_skills)
            except:
                return []
        
        return soft_skills if isinstance(soft_skills, list) else []
    
    def _get_languages(self, user_id: int) -> List[Dict]:
        """Get languages from student_portfolios"""
        portfolio = self.db_manager.query('''
            SELECT languages
            FROM student_portfolios
            WHERE user_id = %s
        ''', (user_id,), one=True)
        
        if not portfolio or not portfolio.get('languages'):
            return [{'language': 'Italian', 'level': 'Native'}]
        
        languages = portfolio.get('languages')
        if isinstance(languages, str):
            try:
                languages = json.loads(languages)
            except:
                return []
        
        return languages if isinstance(languages, list) else []
    
    def _format_project_duration(self, start_date, end_date, is_ongoing: bool) -> str:
        """Format project duration string"""
        if not start_date:
            return 'N/A'
        
        start_str = start_date.strftime('%b %Y') if hasattr(start_date, 'strftime') else str(start_date)
        
        if is_ongoing:
            return f"{start_str} - Present"
        elif end_date:
            end_str = end_date.strftime('%b %Y') if hasattr(end_date, 'strftime') else str(end_date)
            return f"{start_str} - {end_str}"
        else:
            return start_str
    
    def _calculate_completeness(self, candidate_card: Dict) -> int:
        """Calculate profile completeness percentage"""
        score = 0
        max_score = 100
        
        if candidate_card.get('personal_info', {}).get('name'):
            score += 10
        if candidate_card.get('academic_performance', {}).get('average_gpa') != 'N/A':
            score += 15
        if len(candidate_card.get('badges_certifications', [])) > 0:
            score += 15
        if len(candidate_card.get('skills', [])) >= 3:
            score += 20
        if len(candidate_card.get('projects', [])) > 0:
            score += 20
        if len(candidate_card.get('soft_skills', [])) >= 3:
            score += 10
        if len(candidate_card.get('languages', [])) > 0:
            score += 10
        
        return min(score, max_score)
    
    def update_portfolio(self, user_id: int, portfolio_data: Dict) -> bool:
        """Update or create student portfolio"""
        existing = self.db_manager.query('''
            SELECT id FROM student_portfolios WHERE user_id = %s
        ''', (user_id,), one=True)
        
        soft_skills_json = json.dumps(portfolio_data.get('soft_skills', []))
        languages_json = json.dumps(portfolio_data.get('languages', []))
        
        if existing:
            self.db_manager.execute('''
                UPDATE student_portfolios
                SET 
                    bio = %s,
                    soft_skills = %s::jsonb,
                    languages = %s::jsonb,
                    last_updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (
                portfolio_data.get('bio'),
                soft_skills_json,
                languages_json,
                user_id
            ))
        else:
            student = self.db_manager.query('''
                SELECT scuola_id FROM utenti WHERE id = %s
            ''', (user_id,), one=True)
            
            if not student:
                return False
            
            self.db_manager.execute('''
                INSERT INTO student_portfolios 
                (user_id, school_id, bio, soft_skills, languages)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
            ''', (
                user_id,
                student.get('scuola_id'),
                portfolio_data.get('bio'),
                soft_skills_json,
                languages_json
            ))
        
        logger.info(
            event_type='portfolio_updated',
            domain='portfolio',
            user_id=user_id
        )
        
        return True


__all__ = ['StudentPortfolioManager']
