"""
SKAILA - Course Model (ORM)
SQLAlchemy model following best practices
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional

from core.config.database import Base


class Course(Base):
    """
    Course Model - Represents educational courses in SKAILA
    
    Attributes:
        id: Primary key
        nome: Course name (required)
        descrizione: Detailed course description
        professore_id: Foreign key to teacher user
        scuola_id: Foreign key to school (multi-tenant)
        anno_scolastico: Academic year (e.g., "2024-2025")
        attivo: Whether course is currently active
        created_at: Timestamp when course was created
        updated_at: Timestamp when course was last updated
    
    Relationships:
        professore: Many-to-one relationship with User (teacher)
        scuola: Many-to-one relationship with School
    """
    
    __tablename__ = 'courses'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Course Information
    nome = Column(String(200), nullable=False, index=True)
    descrizione = Column(Text, nullable=True)
    anno_scolastico = Column(String(20), nullable=False, index=True)
    
    # Relationships (Foreign Keys)
    professore_id = Column(Integer, ForeignKey('utenti.id', ondelete='SET NULL'), nullable=True)
    scuola_id = Column(Integer, ForeignKey('scuole.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Status
    attivo = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # ORM Relationships (defined if User and School models exist)
    # professore = relationship("User", back_populates="courses_taught")
    # scuola = relationship("School", back_populates="courses")
    
    def __repr__(self) -> str:
        return f"<Course(id={self.id}, nome='{self.nome}', anno='{self.anno_scolastico}')>"
    
    def to_dict(self) -> dict:
        """
        Convert model to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of the course
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'descrizione': self.descrizione,
            'professore_id': self.professore_id,
            'scuola_id': self.scuola_id,
            'anno_scolastico': self.anno_scolastico,
            'attivo': self.attivo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def validate_data(cls, data: dict) -> tuple[bool, Optional[str]]:
        """
        Validate course data before creating/updating
        
        Args:
            data: Dictionary with course data
        
        Returns:
            Tuple (is_valid, error_message)
        """
        if not data.get('nome'):
            return False, "Course name is required"
        
        if len(data.get('nome', '')) > 200:
            return False, "Course name must be less than 200 characters"
        
        if not data.get('scuola_id'):
            return False, "School ID is required"
        
        if not data.get('anno_scolastico'):
            return False, "Academic year is required"
        
        # Validate academic year format (e.g., "2024-2025")
        anno = data.get('anno_scolastico', '')
        if not anno or '-' not in anno:
            return False, "Academic year must be in format 'YYYY-YYYY'"
        
        return True, None


__all__ = ['Course']
