"""
Student Portfolio API Routes
Handles Candidate Card generation and portfolio management
"""

from flask import Blueprint, jsonify, request, session
from shared.middleware.auth import require_login
from services.portfolio.student_portfolio_manager import StudentPortfolioManager
from shared.error_handling import get_logger

logger = get_logger(__name__)
portfolio_bp = Blueprint('portfolio_api', __name__)
portfolio_manager = StudentPortfolioManager()


@portfolio_bp.route('/api/student/portfolio', methods=['GET'])
@require_login
def get_student_portfolio():
    """
    GET /api/student/portfolio
    Returns comprehensive 'Candidate Card' for current student
    
    Query Params:
        - include_grades: Include academic performance (default: false)
        - user_id: Admin override to view other student's portfolio
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    requested_user_id = request.args.get('user_id', type=int)
    include_grades = request.args.get('include_grades', 'false').lower() == 'true'
    
    if requested_user_id and requested_user_id != user_id:
        if ruolo not in ['docente', 'dirigente', 'admin']:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Non hai i permessi per visualizzare questo profilo'
            }), 403
        user_id = requested_user_id
    
    candidate_card = portfolio_manager.generate_candidate_card(
        user_id=user_id,
        include_private=include_grades
    )
    
    if not candidate_card:
        return jsonify({
            'error': 'Not Found',
            'message': 'Profilo studente non trovato'
        }), 404
    
    logger.info(
        event_type='candidate_card_retrieved',
        domain='portfolio',
        user_id=user_id,
        requested_by=session.get('user_id')
    )
    
    return jsonify({
        'success': True,
        'candidate_card': candidate_card
    }), 200


@portfolio_bp.route('/api/student/portfolio', methods=['POST'])
@require_login
def update_student_portfolio():
    """
    POST /api/student/portfolio
    Update student portfolio information (bio, soft skills, languages)
    
    Body:
        {
            "bio": "...",
            "soft_skills": ["Communication", "Leadership"],
            "languages": [{"language": "English", "level": "B2"}]
        }
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Solo gli studenti possono modificare il proprio portfolio'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Dati non validi'
            }), 400
        
        portfolio_data = {
            'bio': data.get('bio', ''),
            'soft_skills': data.get('soft_skills', []),
            'languages': data.get('languages', [])
        }
        
        success = portfolio_manager.update_portfolio(user_id, portfolio_data)
        
        if success:
            logger.info(
                event_type='portfolio_updated',
                domain='portfolio',
                user_id=user_id
            )
            
            return jsonify({
                'success': True,
                'message': 'Portfolio aggiornato con successo'
            }), 200
        else:
            return jsonify({
                'error': 'Update Failed',
                'message': 'Impossibile aggiornare il portfolio'
            }), 500
            
    except Exception as e:
        logger.error(
            event_type='portfolio_update_error',
            domain='portfolio',
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Server Error',
            'message': 'Errore durante l\'aggiornamento del portfolio'
        }), 500


@portfolio_bp.route('/api/student/skills', methods=['POST'])
@require_login
def add_student_skill():
    """
    POST /api/student/skills
    Add a new skill to student profile
    
    Body:
        {
            "skill_name": "Python",
            "skill_category": "technical",
            "proficiency_level": "intermediate"
        }
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Solo gli studenti possono aggiungere competenze'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('skill_name'):
            return jsonify({
                'error': 'Bad Request',
                'message': 'Nome skill richiesto'
            }), 400
        
        from services.database.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        db_manager.execute('''
            INSERT INTO student_skills 
            (user_id, skill_name, skill_category, proficiency_level)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, skill_name) 
            DO UPDATE SET 
                skill_category = EXCLUDED.skill_category,
                proficiency_level = EXCLUDED.proficiency_level
        ''', (
            user_id,
            data.get('skill_name'),
            data.get('skill_category', 'technical'),
            data.get('proficiency_level', 'beginner')
        ))
        
        logger.info(
            event_type='skill_added',
            domain='portfolio',
            user_id=user_id,
            skill_name=data.get('skill_name')
        )
        
        return jsonify({
            'success': True,
            'message': 'Competenza aggiunta con successo'
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='skill_add_error',
            domain='portfolio',
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Server Error',
            'message': 'Errore durante l\'aggiunta della competenza'
        }), 500


@portfolio_bp.route('/api/student/projects', methods=['POST'])
@require_login
def add_student_project():
    """
    POST /api/student/projects
    Add a new project to student portfolio
    
    Body:
        {
            "title": "...",
            "description": "...",
            "project_type": "academic",
            "technologies": ["Python", "Flask"],
            "start_date": "2024-01-01",
            "is_ongoing": false
        }
    """
    user_id = session.get('user_id')
    ruolo = session.get('ruolo')
    
    if ruolo != 'studente':
        return jsonify({
            'error': 'Forbidden',
            'message': 'Solo gli studenti possono aggiungere progetti'
        }), 403
    
    try:
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({
                'error': 'Bad Request',
                'message': 'Titolo progetto richiesto'
            }), 400
        
        from services.database.database_manager import DatabaseManager
        import json
        db_manager = DatabaseManager()
        
        technologies_json = json.dumps(data.get('technologies', []))
        
        db_manager.execute('''
            INSERT INTO student_projects 
            (user_id, title, description, project_type, technologies, 
             start_date, end_date, is_ongoing, achievements, project_url)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('title'),
            data.get('description'),
            data.get('project_type', 'personal'),
            technologies_json,
            data.get('start_date'),
            data.get('end_date'),
            data.get('is_ongoing', False),
            data.get('achievements'),
            data.get('project_url')
        ))
        
        logger.info(
            event_type='project_added',
            domain='portfolio',
            user_id=user_id,
            project_title=data.get('title')
        )
        
        return jsonify({
            'success': True,
            'message': 'Progetto aggiunto con successo'
        }), 200
        
    except Exception as e:
        logger.error(
            event_type='project_add_error',
            domain='portfolio',
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Server Error',
            'message': 'Errore durante l\'aggiunta del progetto'
        }), 500


__all__ = ['portfolio_bp']
