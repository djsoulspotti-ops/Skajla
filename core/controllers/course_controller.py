"""
SKAILA - Course Controller (Business Logic)
Handles all business logic for Course operations following MVC pattern
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from core.models.course import Course
from core.config.database import get_db_session
from core.config.logging_config import setup_logger
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseOperationError,
    DuplicateResourceError
)

logger = setup_logger(__name__)


class CourseController:
    """
    Course Controller - Business logic layer for Course operations
    
    Responsibilities:
        - Validate input data
        - Execute CRUD operations using ORM
        - Handle business rules
        - Manage transactions
        - Log operations
    """
    
    @staticmethod
    def create_course(data: Dict[str, Any]) -> Course:
        """
        Create a new course with validation and error handling
        
        Args:
            data: Dictionary containing course data
                Required keys: nome, scuola_id, anno_scolastico
                Optional keys: descrizione, professore_id, attivo
        
        Returns:
            Created Course object
        
        Raises:
            ValidationError: If data validation fails
            DuplicateResourceError: If course already exists
            DatabaseOperationError: If database operation fails
        
        Example:
            >>> controller = CourseController()
            >>> course_data = {
            ...     'nome': 'Matematica Avanzata',
            ...     'scuola_id': 1,
            ...     'anno_scolastico': '2024-2025',
            ...     'professore_id': 5
            ... }
            >>> course = controller.create_course(course_data)
        """
        # Validate input data
        is_valid, error_msg = Course.validate_data(data)
        if not is_valid:
            logger.warning(f"Course validation failed: {error_msg}", extra={'data': data})
            raise ValidationError(
                f"Invalid course data: {error_msg}",
                context={'validation_error': error_msg, 'provided_data': data}
            )
        
        try:
            with get_db_session() as session:
                # Check for duplicate (same name, school, year)
                existing = session.query(Course).filter(
                    Course.nome == data['nome'],
                    Course.scuola_id == data['scuola_id'],
                    Course.anno_scolastico == data['anno_scolastico']
                ).first()
                
                if existing:
                    logger.warning(
                        f"Duplicate course creation attempted",
                        extra={
                            'nome': data['nome'],
                            'scuola_id': data['scuola_id'],
                            'anno': data['anno_scolastico']
                        }
                    )
                    raise DuplicateResourceError(
                        "Course already exists",
                        context={
                            'existing_id': existing.id,
                            'nome': data['nome'],
                            'scuola_id': data['scuola_id']
                        }
                    )
                
                # Create new course
                course = Course(
                    nome=data['nome'],
                    descrizione=data.get('descrizione'),
                    scuola_id=data['scuola_id'],
                    professore_id=data.get('professore_id'),
                    anno_scolastico=data['anno_scolastico'],
                    attivo=data.get('attivo', True)
                )
                
                session.add(course)
                session.flush()  # Get the ID without committing
                
                logger.info(
                    f"Course created successfully",
                    extra={
                        'course_id': course.id,
                        'nome': course.nome,
                        'scuola_id': course.scuola_id
                    }
                )
                
                return course
                
        except (DuplicateResourceError, ValidationError):
            raise  # Re-raise custom exceptions
        except IntegrityError as e:
            logger.error(
                f"Database integrity error creating course",
                extra={'error': str(e), 'data': data}
            )
            raise DatabaseOperationError(
                "Failed to create course due to database constraint violation",
                context={'error': str(e), 'operation': 'create_course'}
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Database error creating course",
                extra={'error': str(e), 'data': data}
            )
            raise DatabaseOperationError(
                "Database operation failed while creating course",
                context={'error': str(e), 'operation': 'create_course'}
            )
    
    @staticmethod
    def get_course_by_id(course_id: int) -> Course:
        """
        Retrieve a course by ID
        
        Args:
            course_id: The ID of the course to retrieve
        
        Returns:
            Course object
        
        Raises:
            ResourceNotFoundError: If course doesn't exist
            DatabaseOperationError: If database operation fails
        """
        try:
            with get_db_session() as session:
                course = session.query(Course).filter(Course.id == course_id).first()
                
                if not course:
                    logger.warning(f"Course not found", extra={'course_id': course_id})
                    raise ResourceNotFoundError(
                        f"Course with ID {course_id} not found",
                        context={'course_id': course_id}
                    )
                
                logger.debug(f"Course retrieved", extra={'course_id': course_id})
                return course
                
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving course",
                extra={'error': str(e), 'course_id': course_id}
            )
            raise DatabaseOperationError(
                f"Failed to retrieve course with ID {course_id}",
                context={'error': str(e), 'course_id': course_id}
            )
    
    @staticmethod
    def get_courses_by_school(school_id: int, active_only: bool = True) -> List[Course]:
        """
        Get all courses for a specific school
        
        Args:
            school_id: The school ID to filter by
            active_only: If True, return only active courses
        
        Returns:
            List of Course objects
        
        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            with get_db_session() as session:
                query = session.query(Course).filter(Course.scuola_id == school_id)
                
                if active_only:
                    query = query.filter(Course.attivo == True)
                
                courses = query.order_by(Course.nome).all()
                
                logger.debug(
                    f"Retrieved {len(courses)} courses for school",
                    extra={'school_id': school_id, 'count': len(courses)}
                )
                
                return courses
                
        except SQLAlchemyError as e:
            logger.error(
                f"Database error retrieving courses for school",
                extra={'error': str(e), 'school_id': school_id}
            )
            raise DatabaseOperationError(
                f"Failed to retrieve courses for school {school_id}",
                context={'error': str(e), 'school_id': school_id}
            )
    
    @staticmethod
    def update_course(course_id: int, data: Dict[str, Any]) -> Course:
        """
        Update an existing course
        
        Args:
            course_id: The ID of the course to update
            data: Dictionary with fields to update
        
        Returns:
            Updated Course object
        
        Raises:
            ResourceNotFoundError: If course doesn't exist
            ValidationError: If data validation fails
            DatabaseOperationError: If database operation fails
        """
        try:
            with get_db_session() as session:
                course = session.query(Course).filter(Course.id == course_id).first()
                
                if not course:
                    raise ResourceNotFoundError(
                        f"Course with ID {course_id} not found",
                        context={'course_id': course_id}
                    )
                
                # Update allowed fields
                updatable_fields = ['nome', 'descrizione', 'professore_id', 'anno_scolastico', 'attivo']
                updates_made = []
                
                for field in updatable_fields:
                    if field in data and data[field] is not None:
                        setattr(course, field, data[field])
                        updates_made.append(field)
                
                session.flush()
                
                logger.info(
                    f"Course updated successfully",
                    extra={
                        'course_id': course_id,
                        'fields_updated': updates_made
                    }
                )
                
                return course
                
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(
                f"Database error updating course",
                extra={'error': str(e), 'course_id': course_id}
            )
            raise DatabaseOperationError(
                f"Failed to update course with ID {course_id}",
                context={'error': str(e), 'course_id': course_id}
            )
    
    @staticmethod
    def delete_course(course_id: int, soft_delete: bool = True) -> bool:
        """
        Delete a course (soft or hard delete)
        
        Args:
            course_id: The ID of the course to delete
            soft_delete: If True, set attivo=False; if False, physically delete
        
        Returns:
            True if deletion successful
        
        Raises:
            ResourceNotFoundError: If course doesn't exist
            DatabaseOperationError: If database operation fails
        """
        try:
            with get_db_session() as session:
                course = session.query(Course).filter(Course.id == course_id).first()
                
                if not course:
                    raise ResourceNotFoundError(
                        f"Course with ID {course_id} not found",
                        context={'course_id': course_id}
                    )
                
                if soft_delete:
                    course.attivo = False
                    logger.info(f"Course soft deleted", extra={'course_id': course_id})
                else:
                    session.delete(course)
                    logger.info(f"Course hard deleted", extra={'course_id': course_id})
                
                session.flush()
                return True
                
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(
                f"Database error deleting course",
                extra={'error': str(e), 'course_id': course_id}
            )
            raise DatabaseOperationError(
                f"Failed to delete course with ID {course_id}",
                context={'error': str(e), 'course_id': course_id}
            )


__all__ = ['CourseController']
