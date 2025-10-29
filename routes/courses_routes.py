"""
SKAILA - Courses Routes (Views Layer)
Flask routes for Course management following MVC pattern
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, session
from typing import Dict, Any

from core.controllers.course_controller import CourseController
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseOperationError,
    DuplicateResourceError
)
from core.config.logging_config import setup_logger
from shared.middleware.auth import require_login, require_teacher, require_auth

logger = setup_logger(__name__)

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')


# ==================== Web Routes (HTML) ====================

@courses_bp.route('/', methods=['GET'])
@require_login
def list_courses():
    """
    Display all courses for the current school
    
    Returns:
        HTML page with courses list
    """
    try:
        school_id = session.get('school_id')
        if not school_id:
            flash('School ID not found in session', 'error')
            return redirect('/dashboard')
        
        courses = CourseController.get_courses_by_school(school_id, active_only=True)
        
        logger.info(f"Courses list accessed", extra={
            'user_id': session.get('user_id'),
            'school_id': school_id,
            'courses_count': len(courses)
        })
        
        return render_template(
            'courses/list.html',
            user=session,
            courses=courses
        )
        
    except DatabaseOperationError as e:
        logger.error(f"Database error in list_courses: {e}")
        flash('Error loading courses. Please try again.', 'error')
        return redirect('/dashboard')
    except Exception as e:
        logger.error(f"Unexpected error in list_courses: {e}")
        flash('An unexpected error occurred', 'error')
        return redirect('/dashboard')


@courses_bp.route('/create', methods=['GET', 'POST'])
@require_teacher
def create_course():
    """
    Create a new course (Form + Handler)
    
    GET: Show create form
    POST: Process form submission
    
    Returns:
        HTML page or redirect
    """
    if request.method == 'GET':
        return render_template('courses/create.html', user=session)
    
    # POST - Process form
    try:
        school_id = session.get('school_id')
        teacher_id = session.get('user_id')
        
        course_data = {
            'nome': request.form.get('nome'),
            'descrizione': request.form.get('descrizione'),
            'anno_scolastico': request.form.get('anno_scolastico'),
            'scuola_id': school_id,
            'professore_id': teacher_id,
            'attivo': True
        }
        
        course = CourseController.create_course(course_data)
        
        flash(f'Course "{course.nome}" created successfully!', 'success')
        logger.info(f"Course created via web form", extra={
            'course_id': course.id,
            'teacher_id': teacher_id
        })
        
        return redirect(url_for('courses.list_courses'))
        
    except ValidationError as e:
        flash(f'Validation Error: {e.message}', 'error')
        logger.warning(f"Course creation validation failed: {e}")
        return redirect(url_for('courses.create_course'))
    except DuplicateResourceError as e:
        flash(f'Course already exists: {e.message}', 'warning')
        return redirect(url_for('courses.create_course'))
    except DatabaseOperationError as e:
        flash('Database error. Please try again later.', 'error')
        logger.error(f"Database error creating course: {e}")
        return redirect(url_for('courses.create_course'))
    except Exception as e:
        flash('An unexpected error occurred', 'error')
        logger.error(f"Unexpected error creating course: {e}")
        return redirect(url_for('courses.create_course'))


# ==================== API Routes (JSON) ====================

@courses_bp.route('/api/courses', methods=['POST'])
@require_auth
def api_create_course():
    """
    API endpoint to create a new course
    
    Request Body (JSON):
    {
        "nome": "Matematica Avanzata",
        "descrizione": "Corso di matematica per classe 5A",
        "anno_scolastico": "2024-2025",
        "scuola_id": 1,
        "professore_id": 5
    }
    
    Returns:
        JSON response with created course data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Request body must contain JSON data'
            }), 400
        
        course = CourseController.create_course(data)
        
        logger.info(f"Course created via API", extra={
            'course_id': course.id,
            'user_id': session.get('user_id')
        })
        
        return jsonify({
            'success': True,
            'message': 'Course created successfully',
            'data': course.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'message': e.message,
            'context': e.context
        }), 400
    except DuplicateResourceError as e:
        return jsonify({
            'success': False,
            'error': 'Duplicate Resource',
            'message': e.message,
            'context': e.context
        }), 409
    except DatabaseOperationError as e:
        return jsonify({
            'success': False,
            'error': 'Database Error',
            'message': 'An error occurred while creating the course'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in API create course: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@courses_bp.route('/api/courses/<int:course_id>', methods=['GET'])
@require_auth
def api_get_course(course_id: int):
    """
    API endpoint to retrieve a specific course
    
    Args:
        course_id: Course ID from URL
    
    Returns:
        JSON response with course data
    """
    try:
        course = CourseController.get_course_by_id(course_id)
        
        return jsonify({
            'success': True,
            'data': course.to_dict()
        }), 200
        
    except ResourceNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': e.message
        }), 404
    except DatabaseOperationError as e:
        return jsonify({
            'success': False,
            'error': 'Database Error',
            'message': 'An error occurred while retrieving the course'
        }), 500


@courses_bp.route('/api/courses/school/<int:school_id>', methods=['GET'])
@require_auth
def api_get_school_courses(school_id: int):
    """
    API endpoint to retrieve all courses for a school
    
    Args:
        school_id: School ID from URL
    
    Query Parameters:
        active_only: true/false (default: true)
    
    Returns:
        JSON response with list of courses
    """
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        courses = CourseController.get_courses_by_school(school_id, active_only)
        
        return jsonify({
            'success': True,
            'count': len(courses),
            'data': [course.to_dict() for course in courses]
        }), 200
        
    except DatabaseOperationError as e:
        return jsonify({
            'success': False,
            'error': 'Database Error',
            'message': 'An error occurred while retrieving courses'
        }), 500


@courses_bp.route('/api/courses/<int:course_id>', methods=['PUT', 'PATCH'])
@require_auth
def api_update_course(course_id: int):
    """
    API endpoint to update a course
    
    Args:
        course_id: Course ID from URL
    
    Request Body (JSON) - partial updates allowed:
    {
        "nome": "Nuovo Nome",
        "descrizione": "Nuova descrizione",
        "attivo": false
    }
    
    Returns:
        JSON response with updated course data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        course = CourseController.update_course(course_id, data)
        
        logger.info(f"Course updated via API", extra={
            'course_id': course_id,
            'user_id': session.get('user_id')
        })
        
        return jsonify({
            'success': True,
            'message': 'Course updated successfully',
            'data': course.to_dict()
        }), 200
        
    except ResourceNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': e.message
        }), 404
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation Error',
            'message': e.message
        }), 400
    except DatabaseOperationError as e:
        return jsonify({
            'success': False,
            'error': 'Database Error',
            'message': 'An error occurred while updating the course'
        }), 500


@courses_bp.route('/api/courses/<int:course_id>', methods=['DELETE'])
@require_auth
def api_delete_course(course_id: int):
    """
    API endpoint to delete a course
    
    Args:
        course_id: Course ID from URL
    
    Query Parameters:
        hard_delete: true/false (default: false - soft delete)
    
    Returns:
        JSON response confirming deletion
    """
    try:
        hard_delete = request.args.get('hard_delete', 'false').lower() == 'true'
        CourseController.delete_course(course_id, soft_delete=not hard_delete)
        
        logger.info(f"Course deleted via API", extra={
            'course_id': course_id,
            'hard_delete': hard_delete,
            'user_id': session.get('user_id')
        })
        
        return jsonify({
            'success': True,
            'message': 'Course deleted successfully'
        }), 200
        
    except ResourceNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': e.message
        }), 404
    except DatabaseOperationError as e:
        return jsonify({
            'success': False,
            'error': 'Database Error',
            'message': 'An error occurred while deleting the course'
        }), 500


__all__ = ['courses_bp']
