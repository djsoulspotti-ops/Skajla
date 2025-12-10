"""
SKAJLA Behavioral Telemetry Engine
Real-time tracking and analysis of student learning behaviors for early warning system
Part of Feature #1: Smart AI-Tutoring & Early-Warning Engine
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from services.database.database_manager import db_manager
import json
import hashlib
import secrets

from shared.error_handling import (
    DatabaseError,
    get_logger
)

logger = get_logger(__name__)


class TelemetryEngine:
    """
    Tracks and analyzes student behavioral patterns
    to detect struggle and trigger early warnings
    """
    
    STRUGGLE_THRESHOLDS = {
        'high_time_low_accuracy': {
            'min_time_seconds': 120,
            'max_accuracy': 50.0,
            'weight': 0.8
        },
        'multiple_retries': {
            'min_retries': 3,
            'weight': 0.6
        },
        'hint_dependency': {
            'min_hints': 2,
            'max_completion_rate': 60.0,
            'weight': 0.5
        },
        'error_frequency': {
            'error_rate': 0.7,
            'weight': 0.75
        }
    }
    
    def __init__(self):
        """Initialize telemetry engine and create tables if needed"""
        self._init_tables()
        logger.info(
            event_type='telemetry_engine_initialized',
            domain='telemetry',
            message='Telemetry Engine initialized successfully'
        )
    
    def _init_tables(self):
        """Create telemetry tables for both PostgreSQL and SQLite"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if db_manager.db_type == 'postgresql':
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS behavioral_telemetry (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
                            scuola_id INTEGER REFERENCES scuole(id),
                            
                            event_type VARCHAR(50) NOT NULL,
                            event_category VARCHAR(50),
                            
                            session_id VARCHAR(64),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            duration_seconds INTEGER,
                            
                            context_data JSONB,
                            
                            accuracy_score DECIMAL(5,2),
                            confidence_level VARCHAR(20),
                            struggle_indicator BOOLEAN DEFAULT FALSE,
                            
                            device_type VARCHAR(20),
                            user_agent TEXT
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_telemetry_user_time 
                        ON behavioral_telemetry(user_id, timestamp DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_telemetry_event_type 
                        ON behavioral_telemetry(event_type, timestamp DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_telemetry_struggle 
                        ON behavioral_telemetry(struggle_indicator, user_id)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_telemetry_session 
                        ON behavioral_telemetry(session_id)
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS early_warning_alerts (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
                            scuola_id INTEGER REFERENCES scuole(id),
                            
                            alert_type VARCHAR(50) NOT NULL,
                            severity VARCHAR(20) NOT NULL,
                            status VARCHAR(20) DEFAULT 'active',
                            
                            title VARCHAR(200),
                            description TEXT,
                            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            evidence JSONB,
                            recommended_actions JSONB,
                            
                            recovery_path_id INTEGER,
                            
                            acknowledged_by INTEGER REFERENCES utenti(id),
                            acknowledged_at TIMESTAMP,
                            teacher_notes TEXT,
                            
                            resolved_at TIMESTAMP,
                            resolution_method VARCHAR(100)
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_alert_user_status 
                        ON early_warning_alerts(user_id, status, detected_at DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_alert_severity 
                        ON early_warning_alerts(severity, status)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_alert_type 
                        ON early_warning_alerts(alert_type, detected_at DESC)
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS recovery_paths (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
                            alert_id INTEGER,
                            
                            subject VARCHAR(100),
                            weak_topics JSONB,
                            target_competency_level VARCHAR(20),
                            
                            path_steps JSONB,
                            
                            current_step INTEGER DEFAULT 1,
                            completion_status VARCHAR(20) DEFAULT 'in_progress',
                            
                            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            completed_at TIMESTAMP,
                            last_activity_at TIMESTAMP,
                            
                            initial_accuracy DECIMAL(5,2),
                            final_accuracy DECIMAL(5,2),
                            improvement_percentage DECIMAL(5,2)
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_recovery_user 
                        ON recovery_paths(user_id, completion_status)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_recovery_subject 
                        ON recovery_paths(subject, completion_status)
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS telemetry_sessions (
                            session_id VARCHAR(64) PRIMARY KEY,
                            user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
                            
                            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ended_at TIMESTAMP,
                            duration_seconds INTEGER,
                            
                            total_events INTEGER DEFAULT 0,
                            page_views INTEGER DEFAULT 0,
                            tasks_attempted INTEGER DEFAULT 0,
                            tasks_completed INTEGER DEFAULT 0,
                            
                            avg_accuracy DECIMAL(5,2),
                            avg_time_per_task DECIMAL(8,2),
                            struggle_events_count INTEGER DEFAULT 0,
                            
                            engagement_score DECIMAL(5,2),
                            
                            subjects_covered JSONB,
                            device_type VARCHAR(20)
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_session_user 
                        ON telemetry_sessions(user_id, started_at DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_session_engagement 
                        ON telemetry_sessions(engagement_score DESC)
                    ''')
                    
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS behavioral_telemetry (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            scuola_id INTEGER,
                            
                            event_type VARCHAR(50) NOT NULL,
                            event_category VARCHAR(50),
                            
                            session_id VARCHAR(64),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            duration_seconds INTEGER,
                            
                            context_data TEXT,
                            
                            accuracy_score REAL,
                            confidence_level VARCHAR(20),
                            struggle_indicator BOOLEAN DEFAULT 0,
                            
                            device_type VARCHAR(20),
                            user_agent TEXT
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_telemetry_user_time 
                        ON behavioral_telemetry(user_id, timestamp DESC)
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS early_warning_alerts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            scuola_id INTEGER,
                            
                            alert_type VARCHAR(50) NOT NULL,
                            severity VARCHAR(20) NOT NULL,
                            status VARCHAR(20) DEFAULT 'active',
                            
                            title VARCHAR(200),
                            description TEXT,
                            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            evidence TEXT,
                            recommended_actions TEXT,
                            
                            recovery_path_id INTEGER,
                            
                            acknowledged_by INTEGER,
                            acknowledged_at TIMESTAMP,
                            teacher_notes TEXT,
                            
                            resolved_at TIMESTAMP,
                            resolution_method VARCHAR(100)
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS recovery_paths (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            alert_id INTEGER,
                            
                            subject VARCHAR(100),
                            weak_topics TEXT,
                            target_competency_level VARCHAR(20),
                            
                            path_steps TEXT,
                            
                            current_step INTEGER DEFAULT 1,
                            completion_status VARCHAR(20) DEFAULT 'in_progress',
                            
                            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            completed_at TIMESTAMP,
                            last_activity_at TIMESTAMP,
                            
                            initial_accuracy REAL,
                            final_accuracy REAL,
                            improvement_percentage REAL
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS telemetry_sessions (
                            session_id VARCHAR(64) PRIMARY KEY,
                            user_id INTEGER,
                            
                            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ended_at TIMESTAMP,
                            duration_seconds INTEGER,
                            
                            total_events INTEGER DEFAULT 0,
                            page_views INTEGER DEFAULT 0,
                            tasks_attempted INTEGER DEFAULT 0,
                            tasks_completed INTEGER DEFAULT 0,
                            
                            avg_accuracy REAL,
                            avg_time_per_task REAL,
                            struggle_events_count INTEGER DEFAULT 0,
                            
                            engagement_score REAL,
                            
                            subjects_covered TEXT,
                            device_type VARCHAR(20)
                        )
                    ''')
                
                conn.commit()
                logger.info(
                    event_type='telemetry_tables_created',
                    domain='telemetry',
                    message='Telemetry database tables created successfully',
                    db_type=db_manager.db_type
                )
                
        except Exception as e:
            logger.error(
                event_type='telemetry_tables_creation_failed',
                domain='telemetry',
                message=f'Failed to create telemetry tables: {e}',
                error=str(e),
                exc_info=True
            )
            raise
    
    def track_event(
        self,
        user_id: int,
        event_type: str,
        context: Dict[str, Any],
        duration_seconds: Optional[int] = None,
        accuracy_score: Optional[float] = None
    ) -> int:
        """
        Track a behavioral telemetry event
        
        Note: User existence validation is performed at API route level
        to avoid duplicate database queries.
        
        Args:
            user_id: Student ID
            event_type: Type of event (page_view, task_submit, etc.)
            context: Event context data (subject, task_id, etc.)
            duration_seconds: Time spent
            accuracy_score: Performance score (0-100)
        
        Returns:
            event_id: ID of created telemetry event
        """
        try:
            session_id = context.get('session_id') or self._get_or_create_session(user_id, context.get('device_type', 'desktop'))
            
            struggle = self._detect_struggle(
                event_type=event_type,
                duration=duration_seconds,
                accuracy=accuracy_score,
                context=context
            )
            
            scuola_id = self._get_user_school(user_id)
            
            context_json = json.dumps(context) if db_manager.db_type == 'postgresql' else json.dumps(context)
            
            result = db_manager.execute('''
                INSERT INTO behavioral_telemetry (
                    user_id, scuola_id, event_type, event_category,
                    session_id, duration_seconds, context_data,
                    accuracy_score, struggle_indicator, device_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                scuola_id,
                event_type,
                self._categorize_event(event_type),
                session_id,
                duration_seconds,
                context_json,
                accuracy_score,
                struggle,
                context.get('device_type', 'desktop')
            ))
            
            event_id = result.lastrowid if result.lastrowid else 0
            
            self._update_session_metrics(session_id)
            
            # CRITICAL: Always check early warning conditions for learning events
            if event_type in ['task_submit', 'quiz_answer', 'task_start']:
                self._check_early_warning_conditions(user_id, context.get('subject'))
            elif struggle or (accuracy_score is not None and accuracy_score < 50):
                # Also check for other events if struggle detected
                self._check_early_warning_conditions(user_id, context.get('subject'))
            
            return event_id
            
        except Exception as e:
            logger.error(
                event_type='telemetry_tracking_failed',
                domain='telemetry',
                message=f'Failed to track telemetry event: {e}',
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return 0
    
    def _detect_struggle(
        self,
        event_type: str,
        duration: Optional[int],
        accuracy: Optional[float],
        context: Dict[str, Any]
    ) -> bool:
        """
        Detect if event indicates student struggle
        
        Returns:
            True if struggle pattern detected
        """
        if duration and accuracy is not None:
            threshold = self.STRUGGLE_THRESHOLDS['high_time_low_accuracy']
            if duration >= threshold['min_time_seconds'] and accuracy <= threshold['max_accuracy']:
                return True
        
        retry_count = context.get('retry_count', 0)
        if retry_count >= self.STRUGGLE_THRESHOLDS['multiple_retries']['min_retries']:
            return True
        
        hints_used = context.get('hints_used', 0)
        completion_rate = context.get('completion_rate', 100.0)
        threshold = self.STRUGGLE_THRESHOLDS['hint_dependency']
        if hints_used >= threshold['min_hints'] and completion_rate <= threshold['max_completion_rate']:
            return True
        
        error_count = context.get('error_count', 0)
        total_attempts = context.get('total_attempts', 1)
        error_rate = error_count / total_attempts if total_attempts > 0 else 0
        if error_rate >= self.STRUGGLE_THRESHOLDS['error_frequency']['error_rate']:
            return True
        
        return False
    
    def _categorize_event(self, event_type: str) -> str:
        """Categorize event type"""
        categories = {
            'page_view': 'engagement',
            'page_exit': 'engagement',
            'task_start': 'learning',
            'task_submit': 'assessment',
            'quiz_answer': 'assessment',
            'material_open': 'learning',
            'video_watch': 'learning',
            'chat_message': 'interaction'
        }
        return categories.get(event_type, 'other')
    
    def _get_user_school(self, user_id: int) -> Optional[int]:
        """Get user's school ID"""
        try:
            user = db_manager.query(
                'SELECT scuola_id FROM utenti WHERE id = %s',
                (user_id,),
                one=True
            )
            return user['scuola_id'] if user else None
        except Exception:
            return None
    
    def _get_or_create_session(self, user_id: int, device_type: str) -> str:
        """
        Get or create telemetry session - returns None on failure
        
        Note: User existence validation is performed at API route level
        to avoid duplicate database queries.
        """
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
        
        try:
            result = db_manager.execute('''
                INSERT INTO telemetry_sessions (
                    session_id, user_id, device_type, started_at
                ) VALUES (%s, %s, %s, %s)
                RETURNING session_id
            ''', (session_id, user_id, device_type, datetime.now()))
            
            if not result or result.rowcount == 0:
                logger.error(
                    event_type='session_insert_failed',
                    domain='telemetry',
                    user_id=user_id,
                    message='Session insert returned no rows'
                )
                return None
            
            return session_id
            
        except Exception as e:
            logger.error(
                event_type='session_creation_exception',
                domain='telemetry',
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return None
    
    def _update_session_metrics(self, session_id: str):
        """Update session aggregate metrics"""
        try:
            db_manager.execute('''
                UPDATE telemetry_sessions
                SET 
                    total_events = total_events + 1,
                    ended_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
            ''', (session_id,))
        except Exception as e:
            logger.warning(
                event_type='session_update_failed',
                domain='telemetry',
                error=str(e)
            )
    
    def _check_early_warning_conditions(self, user_id: int, subject: Optional[str]):
        """
        Analyze recent telemetry to determine if early warning alert needed
        Works even when subject is None/missing
        """
        try:
            # CRITICAL: Use simplified query that works with or without subject
            recent_struggles = db_manager.query('''
                SELECT 
                    COUNT(*) as struggle_count,
                    AVG(duration_seconds) as avg_time,
                    AVG(accuracy_score) as avg_accuracy
                FROM behavioral_telemetry
                WHERE user_id = %s
                  AND struggle_indicator = TRUE
                  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            ''', (user_id,), one=True) if db_manager.db_type == 'postgresql' else None
            
            if not recent_struggles:
                return
            
            struggle_count = recent_struggles.get('struggle_count', 0)
            avg_accuracy = recent_struggles.get('avg_accuracy', 100.0) or 100.0
            
            # Trigger alert if significant struggle pattern detected
            if struggle_count >= 5:
                # Check if alert already exists for this user (prevent duplicates)
                existing = db_manager.query('''
                    SELECT id FROM early_warning_alerts
                    WHERE user_id = %s
                      AND alert_type = 'struggle_pattern'
                      AND status = 'active'
                    LIMIT 1
                ''', (user_id,), one=True)
                
                if not existing:
                    self._create_early_warning_alert(
                        user_id=user_id,
                        alert_type='struggle_pattern',
                        subject=subject or 'generale',
                        evidence=recent_struggles
                    )
                        
        except Exception as e:
            logger.error(
                event_type='early_warning_check_failed',
                domain='telemetry',
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
    
    def _create_early_warning_alert(
        self,
        user_id: int,
        alert_type: str,
        subject: str,
        evidence: Dict[str, Any]
    ):
        """Create early warning alert"""
        try:
            avg_accuracy = evidence.get('avg_accuracy', 100)
            struggle_count = evidence.get('struggle_count', 0)
            
            if avg_accuracy < 30 or struggle_count > 10:
                severity = 'critical'
            elif avg_accuracy < 50 or struggle_count > 7:
                severity = 'high'
            elif avg_accuracy < 60 or struggle_count > 5:
                severity = 'medium'
            else:
                severity = 'low'
            
            scuola_id = self._get_user_school(user_id)
            
            evidence_json = json.dumps(evidence)
            recommended_actions_json = json.dumps([
                {"action": "teacher_review", "priority": "high"},
                {"action": "recovery_path", "priority": "medium"}
            ])
            
            db_manager.execute('''
                INSERT INTO early_warning_alerts (
                    user_id, scuola_id, alert_type, severity,
                    title, description, evidence, recommended_actions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                scuola_id,
                alert_type,
                severity,
                f"Difficoltà rilevata in {subject}",
                f"Rilevato pattern di difficoltà ripetuta. Media accuracy: {avg_accuracy:.1f}%, {struggle_count} eventi di struggle negli ultimi 7 giorni.",
                evidence_json,
                recommended_actions_json
            ))
            
            logger.info(
                event_type='early_warning_alert_created',
                domain='telemetry',
                user_id=user_id,
                severity=severity,
                subject=subject
            )
            
        except Exception as e:
            logger.error(
                event_type='alert_creation_failed',
                domain='telemetry',
                error=str(e),
                exc_info=True
            )
    
    def get_active_alerts_for_teacher(self, teacher_id: int) -> List[Dict]:
        """
        Get all active early warning alerts for students in teacher's classes
        
        Returns:
            List of alerts with student info and recommended actions
        """
        try:
            teacher_data = db_manager.query(
                'SELECT classe FROM utenti WHERE id = %s',
                (teacher_id,),
                one=True
            )
            
            if not teacher_data:
                return []
            
            alerts = db_manager.query('''
                SELECT 
                    ewa.*,
                    u.nome, u.cognome, u.classe
                FROM early_warning_alerts ewa
                JOIN utenti u ON ewa.user_id = u.id
                WHERE ewa.status = 'active'
                  AND u.classe = %s
                ORDER BY 
                    CASE ewa.severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END,
                    ewa.detected_at DESC
            ''', (teacher_data['classe'],))
            
            formatted_alerts = []
            for alert in alerts:
                try:
                    formatted_alert = dict(alert)
                except (TypeError, ValueError) as e:
                    logger.warning(
                        event_type='alert_conversion_failed',
                        domain='telemetry',
                        error=str(e),
                        alert_type=type(alert).__name__
                    )
                    continue
                
                nome = formatted_alert.get('nome', '')
                cognome = formatted_alert.get('cognome', '')
                formatted_alert['student_name'] = f"{nome} {cognome}".strip()
                
                evidence = formatted_alert.get('evidence')
                if evidence:
                    try:
                        formatted_alert['evidence'] = json.loads(evidence) if isinstance(evidence, str) else evidence
                    except:
                        formatted_alert['evidence'] = {}
                else:
                    formatted_alert['evidence'] = {}
                    
                actions = formatted_alert.get('recommended_actions')
                if actions:
                    try:
                        formatted_alert['recommended_actions'] = json.loads(actions) if isinstance(actions, str) else actions
                    except:
                        formatted_alert['recommended_actions'] = []
                else:
                    formatted_alert['recommended_actions'] = []
                
                formatted_alerts.append(formatted_alert)
            
            return formatted_alerts
            
        except Exception as e:
            logger.error(
                event_type='get_alerts_failed',
                domain='telemetry',
                error=str(e),
                exc_info=True
            )
            return []


# Lazy initialization wrapper to avoid database operations at import time
# Critical for Autoscale health checks - Flask must respond before heavy init
import threading

class _LazyTelemetryEngine:
    """Defers TelemetryEngine initialization until first access.
    Thread-safe with double-checked locking.
    """
    _instance = None
    _initialized = False
    _lock = threading.Lock()
    
    def __getattr__(self, name):
        if not self._initialized:
            self._initialize()
        return getattr(self._instance, name)
    
    def _initialize(self):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self._instance = TelemetryEngine()
            self._initialized = True

telemetry_engine = _LazyTelemetryEngine()
