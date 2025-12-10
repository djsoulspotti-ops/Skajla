# SKAJLA Super-App Transformation
## CTO/Product Architect Master Plan

**Document Type**: Technical Architecture & Implementation Roadmap  
**Author**: Chief Technology Officer  
**Date**: November 2025  
**Objective**: Transform SKAJLA into a Super-App that crushes ClasseViva and WeSchool

---

## 🎯 Executive Summary

### Current State Analysis

**SKAJLA Today:**
- ✅ **Strong Foundation**: Flask + PostgreSQL multi-tenant architecture
- ✅ **Real-time Infrastructure**: Socket.IO for messaging and presence
- ✅ **Native AI**: SKAJLA AI Brain Engine (no external dependencies)
- ✅ **Gamification**: Production-ready XP system with 40+ actions
- ✅ **Premium UX**: Bento Grid dashboards with collapsible sidebar
- ✅ **Feature Flags**: Modular system for per-school customization

**Competitors' Weaknesses:**
1. **ClasseViva**: Passive data storage, desktop-centric, paper-heavy bureaucracy
2. **WeSchool**: Basic LMS, no AI tutoring, minimal gamification, boring UX

### Transformation Strategy

Transform SKAJLA by implementing **3 Killer Features** that exploit competitor weaknesses:

1. **🧠 Smart AI-Tutoring & Early-Warning Engine** → Beat them on **Prevention**
2. **📱 Gen-Z Mobile-First UX Engine** → Beat them on **Engagement**
3. **📄 Compliance & Paperless Engine** → Beat them on **Efficiency**

---

## 🏗️ Current Architecture Analysis

### Database Layer (PostgreSQL + SQLite)

**Current Schema:**
```
Core Tables:
├── utenti (users)
├── scuole (schools) - multi-tenant
├── classi (classes)
├── chat + partecipanti_chat (messaging)
├── registro_presenze/voti/note (electronic register)
├── ai_conversations + ai_response_cache (AI)
├── user_gamification + daily_analytics (gamification)
├── teaching_materials (materials)
├── study_sessions (timer)
├── schedules + school_wide_events (calendar)
└── school_features (feature flags)
```

**ORM**: SQLAlchemy with `DatabaseManager` abstraction  
**Connection Pooling**: 10-50 concurrent connections (Neon PostgreSQL)  
**Performance**: Indexed queries, JSONB for flexible metadata

### Backend Architecture (Flask)

**Modular Service Layer:**
```
services/
├── ai/ (AI Brain, Coaching, Quiz, Insights)
├── auth_service.py (authentication)
├── gamification/ (XP engine, levels, badges)
├── school/ (multi-tenant, feature flags)
├── database/ (DatabaseManager, migrations)
├── calendar/ (smart calendar system)
└── utils/ (monitoring, email, admin dashboard)
```

**Real-Time**: Socket.IO with event-driven architecture  
**Error Handling**: Centralized exception framework with structured logging  
**Security**: CSRF protection, multi-tenant isolation, rate limiting

### Frontend Architecture

**Current Stack:**
- **HTML5 + CSS3**: Responsive Bento Grid layout
- **Design Tokens**: CSS custom properties (`tokens.css`)
- **JavaScript**: Vanilla JS + Socket.IO client
- **Libraries**: GSAP (animations), FullCalendar.js (calendar), Chart.js (analytics)
- **Mobile**: Responsive breakpoints, NOT yet PWA

**Current Limitations:**
- ❌ **Not Progressive Web App** (no Service Workers)
- ❌ **No vertical feed** (static card layouts)
- ❌ **No offline support**
- ❌ **No push notifications** (only in-app)
- ❌ **Desktop-first** (mobile is responsive, not optimized)

---

## 🚀 KILLER FEATURE #1: Smart AI-Tutoring & Early-Warning Engine

### Problem Statement

**Competitors are PASSIVE:**
- ClasseViva stores grades but doesn't prevent failure
- WeSchool provides content but doesn't track struggle patterns
- No behavioral telemetry to detect early warning signs

**Our Solution:** **Behavioral Telemetry System** that predicts and prevents student failure.

---

### Architecture Design

#### 1.1 Database Schema Changes

**New Tables:**

```sql
-- Behavioral Telemetry Events Table
CREATE TABLE behavioral_telemetry (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
    scuola_id INTEGER REFERENCES scuole(id),
    
    -- Event metadata
    event_type VARCHAR(50) NOT NULL,
    -- Types: 'page_view', 'task_start', 'task_submit', 'quiz_answer', 
    --        'material_open', 'video_watch', 'chat_message', 'click_action'
    
    event_category VARCHAR(50), 
    -- Categories: 'learning', 'engagement', 'assessment', 'interaction'
    
    -- Telemetry data
    session_id VARCHAR(64),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER, -- Time spent on task/page
    
    -- Context data (JSONB for flexibility)
    context_data JSONB,
    -- Example: {
    --   "subject": "matematica",
    --   "task_id": 123,
    --   "difficulty": "medium",
    --   "clicks_count": 15,
    --   "scroll_depth": 78,
    --   "completion_rate": 0.65,
    --   "error_count": 3,
    --   "hints_used": 2,
    --   "retry_count": 1
    -- }
    
    -- Performance indicators
    accuracy_score DECIMAL(5,2), -- 0.00 to 100.00
    confidence_level VARCHAR(20), -- 'high', 'medium', 'low'
    struggle_indicator BOOLEAN DEFAULT FALSE,
    
    -- Device context
    device_type VARCHAR(20), -- 'mobile', 'tablet', 'desktop'
    user_agent TEXT,
    
    -- Indexes
    INDEX idx_telemetry_user_time (user_id, timestamp DESC),
    INDEX idx_telemetry_event_type (event_type, timestamp DESC),
    INDEX idx_telemetry_struggle (struggle_indicator, user_id),
    INDEX idx_telemetry_session (session_id),
    INDEX idx_telemetry_subject (((context_data->>'subject')))
);

-- Early Warning Alerts Table
CREATE TABLE early_warning_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
    scuola_id INTEGER REFERENCES scuole(id),
    
    -- Alert metadata
    alert_type VARCHAR(50) NOT NULL,
    -- Types: 'struggle_pattern', 'engagement_drop', 'grade_decline', 
    --        'attendance_risk', 'deadline_risk', 'burnout_signal'
    
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved', 'dismissed'
    
    -- Alert details
    title VARCHAR(200),
    description TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Evidence data (what triggered this alert)
    evidence JSONB,
    -- Example: {
    --   "pattern": "high_time_low_accuracy",
    --   "metrics": {
    --     "avg_time_on_task": 45.2,
    --     "avg_accuracy": 42.5,
    --     "error_frequency": 0.78,
    --     "retry_count": 5
    --   },
    --   "period": "last_7_days",
    --   "subject": "matematica",
    --   "affected_topics": ["algebra", "equazioni"]
    -- }
    
    -- AI-generated recommendations
    recommended_actions JSONB,
    -- Example: [
    --   {"action": "micro_lesson", "topic": "equazioni_base", "duration_min": 10},
    --   {"action": "peer_tutoring", "matcher": "class_top_performer"},
    --   {"action": "teacher_intervention", "urgency": "medium"}
    -- ]
    
    recovery_path_id INTEGER REFERENCES recovery_paths(id),
    
    -- Teacher interaction
    acknowledged_by INTEGER REFERENCES utenti(id),
    acknowledged_at TIMESTAMP,
    teacher_notes TEXT,
    
    -- Resolution
    resolved_at TIMESTAMP,
    resolution_method VARCHAR(100),
    
    -- Indexes
    INDEX idx_alert_user_status (user_id, status, detected_at DESC),
    INDEX idx_alert_severity (severity, status),
    INDEX idx_alert_type (alert_type, detected_at DESC)
);

-- Recovery Paths Table (AI-generated learning paths)
CREATE TABLE recovery_paths (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
    alert_id INTEGER REFERENCES early_warning_alerts(id),
    
    -- Path metadata
    subject VARCHAR(100),
    weak_topics JSONB, -- Array of topic IDs/names
    target_competency_level VARCHAR(20), -- 'basic', 'intermediate', 'advanced'
    
    -- Path structure
    path_steps JSONB,
    -- Example: [
    --   {
    --     "step": 1,
    --     "type": "micro_lesson",
    --     "title": "Algebra Base - Fondamenti",
    --     "content_id": 123,
    --     "estimated_duration_min": 10,
    --     "required_accuracy": 80,
    --     "resources": ["video_456", "quiz_789"]
    --   },
    --   {
    --     "step": 2,
    --     "type": "practice_quiz",
    --     "title": "Quiz Ripassone Algebra",
    --     "quiz_id": 789,
    --     "passing_score": 70
    --   }
    -- ]
    
    -- Progress tracking
    current_step INTEGER DEFAULT 1,
    completion_status VARCHAR(20) DEFAULT 'in_progress', 
    -- 'in_progress', 'completed', 'abandoned', 'expired'
    
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    
    -- Effectiveness metrics
    initial_accuracy DECIMAL(5,2),
    final_accuracy DECIMAL(5,2),
    improvement_percentage DECIMAL(5,2),
    
    -- Indexes
    INDEX idx_recovery_user (user_id, completion_status),
    INDEX idx_recovery_subject (subject, completion_status)
);

-- Telemetry Sessions Table (aggregate session metrics)
CREATE TABLE telemetry_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id INTEGER REFERENCES utenti(id) ON DELETE CASCADE,
    
    -- Session metadata
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Aggregated metrics
    total_events INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    tasks_attempted INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    
    -- Performance aggregates
    avg_accuracy DECIMAL(5,2),
    avg_time_per_task DECIMAL(8,2),
    struggle_events_count INTEGER DEFAULT 0,
    
    -- Engagement score (calculated)
    engagement_score DECIMAL(5,2),
    -- Formula: (tasks_completed / tasks_attempted) * 100 * (1 - struggle_rate)
    
    -- Context
    subjects_covered JSONB, -- Array of subjects touched in this session
    device_type VARCHAR(20),
    
    INDEX idx_session_user (user_id, started_at DESC),
    INDEX idx_session_engagement (engagement_score DESC)
);
```

**Schema Additions to Existing Tables:**

```sql
-- Add struggle tracking to existing quiz results
ALTER TABLE quiz_results ADD COLUMN IF NOT EXISTS 
    struggle_indicators JSONB;
-- Example: {"high_time": true, "many_retries": true, "hint_dependency": true}

-- Add telemetry reference to ai_conversations
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS 
    triggered_by_alert_id INTEGER REFERENCES early_warning_alerts(id);

-- Add early warning flags to user_gamification
ALTER TABLE user_gamification ADD COLUMN IF NOT EXISTS 
    has_active_alerts BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS
    last_alert_check TIMESTAMP;
```

---

#### 1.2 Backend Service: Telemetry Engine

**New Module:** `services/telemetry/telemetry_engine.py`

```python
"""
SKAJLA Behavioral Telemetry Engine
Real-time tracking and analysis of student learning behaviors
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database_manager import db_manager
import json
import hashlib

class TelemetryEngine:
    """
    Tracks and analyzes student behavioral patterns
    to detect struggle and trigger early warnings
    """
    
    # Struggle pattern thresholds
    STRUGGLE_THRESHOLDS = {
        'high_time_low_accuracy': {
            'min_time_seconds': 120,  # > 2 minutes on task
            'max_accuracy': 50.0,     # < 50% accuracy
            'weight': 0.8             # High severity
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
            'error_rate': 0.7,  # > 70% error rate
            'weight': 0.75
        }
    }
    
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
        
        Args:
            user_id: Student ID
            event_type: Type of event (page_view, task_submit, etc.)
            context: Event context data (subject, task_id, etc.)
            duration_seconds: Time spent
            accuracy_score: Performance score (0-100)
        
        Returns:
            event_id: ID of created telemetry event
        """
        # Generate session ID if not exists
        session_id = context.get('session_id') or self._get_or_create_session(user_id)
        
        # Detect struggle indicator
        struggle = self._detect_struggle(
            event_type=event_type,
            duration=duration_seconds,
            accuracy=accuracy_score,
            context=context
        )
        
        # Insert telemetry event
        event_id = db_manager.execute('''
            INSERT INTO behavioral_telemetry (
                user_id, scuola_id, event_type, event_category,
                session_id, duration_seconds, context_data,
                accuracy_score, struggle_indicator, device_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_id,
            self._get_user_school(user_id),
            event_type,
            self._categorize_event(event_type),
            session_id,
            duration_seconds,
            json.dumps(context),
            accuracy_score,
            struggle,
            context.get('device_type', 'desktop')
        ), returning=True)['id']
        
        # Update session aggregates
        self._update_session_metrics(session_id)
        
        # Check if early warning should be triggered
        if struggle or accuracy_score and accuracy_score < 50:
            self._check_early_warning_conditions(user_id, context.get('subject'))
        
        return event_id
    
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
        # Pattern 1: High time + Low accuracy
        if duration and accuracy is not None:
            threshold = self.STRUGGLE_THRESHOLDS['high_time_low_accuracy']
            if duration >= threshold['min_time_seconds'] and \
               accuracy <= threshold['max_accuracy']:
                return True
        
        # Pattern 2: Multiple retries
        retry_count = context.get('retry_count', 0)
        if retry_count >= self.STRUGGLE_THRESHOLDS['multiple_retries']['min_retries']:
            return True
        
        # Pattern 3: Hint dependency
        hints_used = context.get('hints_used', 0)
        completion_rate = context.get('completion_rate', 100.0)
        threshold = self.STRUGGLE_THRESHOLDS['hint_dependency']
        if hints_used >= threshold['min_hints'] and \
           completion_rate <= threshold['max_completion_rate']:
            return True
        
        # Pattern 4: High error frequency
        error_count = context.get('error_count', 0)
        total_attempts = context.get('total_attempts', 1)
        error_rate = error_count / total_attempts if total_attempts > 0 else 0
        if error_rate >= self.STRUGGLE_THRESHOLDS['error_frequency']['error_rate']:
            return True
        
        return False
    
    def _check_early_warning_conditions(self, user_id: int, subject: Optional[str]):
        """
        Analyze recent telemetry to determine if early warning alert needed
        
        Triggers alert if patterns detected over recent period (7 days)
        """
        # Get recent struggle events
        recent_struggles = db_manager.query('''
            SELECT 
                COUNT(*) as struggle_count,
                AVG(duration_seconds) as avg_time,
                AVG(accuracy_score) as avg_accuracy,
                context_data->>'subject' as subject,
                array_agg(DISTINCT context_data->>'topic') as topics
            FROM behavioral_telemetry
            WHERE user_id = %s
              AND struggle_indicator = TRUE
              AND timestamp >= NOW() - INTERVAL '7 days'
              AND (%s IS NULL OR context_data->>'subject' = %s)
            GROUP BY context_data->>'subject'
        ''', (user_id, subject, subject))
        
        for struggle_data in recent_struggles:
            # Threshold: 5+ struggle events in 7 days on same subject
            if struggle_data['struggle_count'] >= 5:
                # Check if alert already exists
                existing = db_manager.query('''
                    SELECT id FROM early_warning_alerts
                    WHERE user_id = %s
                      AND alert_type = 'struggle_pattern'
                      AND status = 'active'
                      AND evidence->>'subject' = %s
                ''', (user_id, struggle_data['subject']), one=True)
                
                if not existing:
                    # Create new alert
                    self._create_early_warning_alert(
                        user_id=user_id,
                        alert_type='struggle_pattern',
                        subject=struggle_data['subject'],
                        evidence=struggle_data
                    )
    
    def _create_early_warning_alert(
        self,
        user_id: int,
        alert_type: str,
        subject: str,
        evidence: Dict[str, Any]
    ):
        """
        Create early warning alert and generate recovery path
        """
        # Determine severity based on metrics
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
        
        # Generate recommended actions
        recommended_actions = self._generate_recovery_actions(
            user_id=user_id,
            subject=subject,
            weak_topics=evidence.get('topics', []),
            severity=severity
        )
        
        # Create alert
        alert_id = db_manager.execute('''
            INSERT INTO early_warning_alerts (
                user_id, scuola_id, alert_type, severity,
                title, description, evidence, recommended_actions
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_id,
            self._get_user_school(user_id),
            alert_type,
            severity,
            f"Difficoltà rilevata in {subject}",
            f"Rilevato pattern di difficoltà ripetuta in {subject}. "
            f"Media accuracy: {avg_accuracy:.1f}%, {struggle_count} eventi di struggle negli ultimi 7 giorni.",
            json.dumps(evidence),
            json.dumps(recommended_actions)
        ), returning=True)['id']
        
        # Generate recovery path
        recovery_path_id = self._generate_recovery_path(
            user_id=user_id,
            alert_id=alert_id,
            subject=subject,
            weak_topics=evidence.get('topics', [])
        )
        
        # Update alert with recovery path
        db_manager.execute('''
            UPDATE early_warning_alerts
            SET recovery_path_id = %s
            WHERE id = %s
        ''', (recovery_path_id, alert_id))
        
        # Notify teacher (real-time Socket.IO event)
        self._notify_teacher_of_alert(user_id, alert_id, severity)
        
        return alert_id
    
    def _generate_recovery_path(
        self,
        user_id: int,
        alert_id: int,
        subject: str,
        weak_topics: List[str]
    ) -> int:
        """
        Generate AI-powered recovery path with micro-lessons
        
        Returns:
            recovery_path_id
        """
        # Get student's current competency level
        current_level = self._assess_competency_level(user_id, subject)
        
        # Build recovery path steps
        path_steps = []
        
        # Step 1: Micro-lesson on weak topic
        for i, topic in enumerate(weak_topics[:3], 1):  # Max 3 topics
            path_steps.append({
                "step": len(path_steps) + 1,
                "type": "micro_lesson",
                "title": f"{topic.title()} - Fondamenti",
                "content_id": self._find_micro_lesson(subject, topic),
                "estimated_duration_min": 10,
                "required_accuracy": 70,
                "resources": self._find_resources(subject, topic)
            })
            
            # Step 2: Practice quiz after each lesson
            path_steps.append({
                "step": len(path_steps) + 1,
                "type": "practice_quiz",
                "title": f"Quiz di Ripasso - {topic.title()}",
                "quiz_id": self._find_quiz(subject, topic, difficulty='easy'),
                "passing_score": 70,
                "max_attempts": 3
            })
        
        # Final step: Comprehensive assessment
        path_steps.append({
            "step": len(path_steps) + 1,
            "type": "assessment",
            "title": f"Verifica Finale - {subject.title()}",
            "quiz_id": self._find_quiz(subject, weak_topics, difficulty='medium'),
            "passing_score": 75,
            "completion_reward_xp": 100
        })
        
        # Create recovery path
        recovery_path_id = db_manager.execute('''
            INSERT INTO recovery_paths (
                user_id, alert_id, subject, weak_topics,
                target_competency_level, path_steps, current_step
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_id,
            alert_id,
            subject,
            json.dumps(weak_topics),
            current_level,
            json.dumps(path_steps),
            1
        ), returning=True)['id']
        
        return recovery_path_id
    
    def get_active_alerts_for_teacher(self, teacher_id: int) -> List[Dict]:
        """
        Get all active early warning alerts for students in teacher's classes
        
        Returns:
            List of alerts with student info and recommended actions
        """
        alerts = db_manager.query('''
            SELECT 
                ewa.*,
                u.nome, u.cognome, u.classe,
                rp.path_steps, rp.current_step, rp.completion_status
            FROM early_warning_alerts ewa
            JOIN utenti u ON ewa.user_id = u.id
            LEFT JOIN recovery_paths rp ON ewa.recovery_path_id = rp.id
            WHERE ewa.status = 'active'
              AND u.classe IN (
                  SELECT DISTINCT classe FROM utenti WHERE id = %s
                  -- Assumes teacher sees students in their classes
              )
            ORDER BY 
                CASE ewa.severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                ewa.detected_at DESC
        ''', (teacher_id,))
        
        return alerts

# Global instance
telemetry_engine = TelemetryEngine()
```

---

#### 1.3 Frontend Integration: Telemetry Tracker

**New JavaScript Module:** `static/js/telemetry-tracker.js`

```javascript
/**
 * SKAJLA Behavioral Telemetry Tracker
 * Tracks student interactions and sends to backend
 */

class TelemetryTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.currentTaskStart = null;
        this.eventQueue = [];
        this.flushInterval = 5000; // Send events every 5 seconds
        
        this.init();
    }
    
    init() {
        // Start session
        this.startSession();
        
        // Setup event listeners
        this.setupPageViewTracking();
        this.setupTaskTracking();
        this.setupInteractionTracking();
        
        // Start periodic flush
        setInterval(() => this.flushEvents(), this.flushInterval);
        
        // Flush on page unload
        window.addEventListener('beforeunload', () => this.flushEvents(true));
    }
    
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    startSession() {
        fetch('/api/telemetry/session/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: this.sessionId,
                device_type: this.getDeviceType(),
                user_agent: navigator.userAgent
            })
        });
    }
    
    trackEvent(eventType, context, options = {}) {
        const event = {
            event_type: eventType,
            context: {
                ...context,
                session_id: this.sessionId,
                device_type: this.getDeviceType(),
                timestamp: new Date().toISOString()
            },
            duration_seconds: options.duration,
            accuracy_score: options.accuracy
        };
        
        this.eventQueue.push(event);
        
        // Immediate flush for critical events
        if (options.immediate) {
            this.flushEvents();
        }
    }
    
    setupTaskTracking() {
        // Track quiz/assignment start
        document.addEventListener('task-start', (e) => {
            this.currentTaskStart = Date.now();
            this.trackEvent('task_start', {
                task_id: e.detail.task_id,
                task_type: e.detail.task_type,
                subject: e.detail.subject,
                difficulty: e.detail.difficulty
            });
        });
        
        // Track quiz/assignment submission
        document.addEventListener('task-submit', (e) => {
            const duration = this.currentTaskStart 
                ? Math.floor((Date.now() - this.currentTaskStart) / 1000) 
                : null;
            
            this.trackEvent('task_submit', {
                task_id: e.detail.task_id,
                task_type: e.detail.task_type,
                subject: e.detail.subject,
                clicks_count: e.detail.clicks || 0,
                error_count: e.detail.errors || 0,
                retry_count: e.detail.retries || 0,
                hints_used: e.detail.hints || 0,
                completion_rate: e.detail.completion_rate || 100
            }, {
                duration: duration,
                accuracy: e.detail.accuracy,
                immediate: true // Flush immediately
            });
            
            this.currentTaskStart = null;
        });
    }
    
    setupPageViewTracking() {
        // Track page views
        this.trackEvent('page_view', {
            page_url: window.location.pathname,
            page_title: document.title,
            referrer: document.referrer
        });
        
        // Track time on page
        let pageStartTime = Date.now();
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Math.floor((Date.now() - pageStartTime) / 1000);
            this.trackEvent('page_exit', {
                page_url: window.location.pathname,
                time_on_page: timeOnPage
            }, {immediate: true});
        });
    }
    
    setupInteractionTracking() {
        // Track material opens
        document.addEventListener('material-open', (e) => {
            this.trackEvent('material_open', {
                material_id: e.detail.material_id,
                material_type: e.detail.type,
                subject: e.detail.subject
            });
        });
        
        // Track video watching
        document.addEventListener('video-watch', (e) => {
            this.trackEvent('video_watch', {
                video_id: e.detail.video_id,
                watch_percentage: e.detail.percentage,
                subject: e.detail.subject
            }, {
                duration: e.detail.duration_seconds
            });
        });
    }
    
    async flushEvents(synchronous = false) {
        if (this.eventQueue.length === 0) return;
        
        const eventsToSend = [...this.eventQueue];
        this.eventQueue = [];
        
        const sendRequest = () => {
            return fetch('/api/telemetry/events/batch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({events: eventsToSend}),
                keepalive: synchronous // Keep connection alive for beforeunload
            });
        };
        
        if (synchronous) {
            // Synchronous send for page unload
            navigator.sendBeacon('/api/telemetry/events/batch', 
                JSON.stringify({events: eventsToSend}));
        } else {
            // Async send
            await sendRequest();
        }
    }
    
    getDeviceType() {
        const width = window.innerWidth;
        if (width < 768) return 'mobile';
        if (width < 1024) return 'tablet';
        return 'desktop';
    }
}

// Initialize tracker
if (window.userLoggedIn) {
    window.telemetryTracker = new TelemetryTracker();
}
```

**Usage in Quiz Component:**

```javascript
// In quiz.js
function submitQuiz() {
    const quizData = collectQuizData();
    const accuracy = calculateAccuracy(quizData);
    
    // Dispatch telemetry event
    document.dispatchEvent(new CustomEvent('task-submit', {
        detail: {
            task_id: quizId,
            task_type: 'quiz',
            subject: currentSubject,
            accuracy: accuracy,
            errors: quizData.errorCount,
            retries: quizData.retryCount,
            hints: quizData.hintsUsed,
            completion_rate: quizData.completionRate,
            clicks: quizData.clickCount
        }
    }));
    
    // Submit quiz normally
    submitQuizToServer(quizData);
}
```

---

#### 1.4 Teacher Dashboard: Early Warning Panel

**New Route:** `routes/early_warning_routes.py`

```python
from flask import Blueprint, render_template, jsonify, request
from services.telemetry.telemetry_engine import telemetry_engine
from shared.decorators import require_login, require_role

early_warning_bp = Blueprint('early_warning', __name__, url_prefix='/early-warning')

@early_warning_bp.route('/dashboard')
@require_login
@require_role('docente')
def early_warning_dashboard():
    """Dashboard for teachers to view early warning alerts"""
    teacher_id = session.get('user_id')
    
    # Get active alerts
    alerts = telemetry_engine.get_active_alerts_for_teacher(teacher_id)
    
    # Categorize by severity
    critical_alerts = [a for a in alerts if a['severity'] == 'critical']
    high_alerts = [a for a in alerts if a['severity'] == 'high']
    medium_alerts = [a for a in alerts if a['severity'] == 'medium']
    
    return render_template('early_warning_dashboard.html',
        critical_alerts=critical_alerts,
        high_alerts=high_alerts,
        medium_alerts=medium_alerts,
        total_alerts=len(alerts)
    )

@early_warning_bp.route('/alert/<int:alert_id>/acknowledge', methods=['POST'])
@require_login
@require_role('docente')
def acknowledge_alert(alert_id):
    """Teacher acknowledges an alert"""
    teacher_id = session.get('user_id')
    notes = request.json.get('notes', '')
    
    db_manager.execute('''
        UPDATE early_warning_alerts
        SET status = 'acknowledged',
            acknowledged_by = %s,
            acknowledged_at = NOW(),
            teacher_notes = %s
        WHERE id = %s
    ''', (teacher_id, notes, alert_id))
    
    return jsonify({"success": True})
```

**New Template:** `templates/early_warning_dashboard.html`

```html
<!-- Early Warning Dashboard for Teachers -->
<div class="early-warning-dashboard">
    <h1>🚨 Early Warning System</h1>
    <p class="subtitle">Studenti che necessitano intervento</p>
    
    <!-- Critical Alerts -->
    {% if critical_alerts %}
    <section class="alert-section critical">
        <h2>🔴 Critici ({{ critical_alerts|length }})</h2>
        {% for alert in critical_alerts %}
        <div class="alert-card critical">
            <div class="alert-header">
                <div class="student-info">
                    <strong>{{ alert.nome }} {{ alert.cognome }}</strong>
                    <span class="class-badge">{{ alert.classe }}</span>
                </div>
                <span class="severity-badge critical">URGENTE</span>
            </div>
            <div class="alert-body">
                <h3>{{ alert.title }}</h3>
                <p>{{ alert.description }}</p>
                
                <!-- Evidence -->
                <div class="evidence">
                    <div class="metric">
                        <span class="label">Media Accuracy:</span>
                        <span class="value">{{ alert.evidence.avg_accuracy|round(1) }}%</span>
                    </div>
                    <div class="metric">
                        <span class="label">Eventi Struggle:</span>
                        <span class="value">{{ alert.evidence.struggle_count }}</span>
                    </div>
                </div>
                
                <!-- Recommended Actions -->
                <div class="recommendations">
                    <h4>Azioni Raccomandate:</h4>
                    <ul>
                        {% for action in alert.recommended_actions %}
                        <li>{{ action.description }}</li>
                        {% endfor %}
                    </ul>
                </div>
                
                <!-- Recovery Path -->
                {% if alert.path_steps %}
                <div class="recovery-path">
                    <h4>Percorso di Recupero Generato:</h4>
                    <div class="path-progress">
                        Step {{ alert.current_step }} / {{ alert.path_steps|length }}
                    </div>
                </div>
                {% endif %}
            </div>
            <div class="alert-actions">
                <button class="btn-acknowledge" data-alert-id="{{ alert.id }}">
                    <i class="fas fa-check"></i> Prendi in Carico
                </button>
                <a href="/chat/student/{{ alert.user_id }}" class="btn-message">
                    <i class="fas fa-comment"></i> Messaggio Studente
                </a>
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}
    
    <!-- Similar sections for high and medium alerts -->
</div>
```

---

### Implementation Roadmap: Feature #1

**Phase 1: Foundation (Week 1-2)**
- ✅ Create database schema (4 new tables)
- ✅ Build TelemetryEngine backend service
- ✅ Create telemetry API endpoints

**Phase 2: Frontend Tracking (Week 3)**
- ✅ Implement telemetry-tracker.js
- ✅ Integrate with quiz system
- ✅ Add tracking to materials/video players

**Phase 3: AI & Alerts (Week 4-5)**
- ✅ Implement struggle detection algorithms
- ✅ Build early warning alert system
- ✅ Create recovery path generator

**Phase 4: Teacher Dashboard (Week 6)**
- ✅ Build early warning dashboard
- ✅ Real-time Socket.IO notifications
- ✅ Recovery path management UI

**Phase 5: Testing & Tuning (Week 7-8)**
- ✅ A/B test thresholds
- ✅ Tune ML algorithms
- ✅ Collect teacher feedback

---

## 📱 KILLER FEATURE #2: Gen-Z Mobile-First UX Engine

### Problem Statement

**Competitors are BORING and DESKTOP-CENTRIC:**
- ClasseViva: ugly 2010-era desktop UI
- WeSchool: basic responsive, no native feel
- Both: zero short-form video, no social engagement

**Our Solution:** **TikTok-style vertical feed PWA** with heavy gamification

---

### Architecture Design

#### 2.1 Progressive Web App (PWA) Transformation

**Key Changes:**

```
Frontend Architecture Transformation:
├── Service Worker for offline support
├── App Manifest for installability
├── Push Notifications API
├── Background Sync
└── Cache-First Strategy
```

**New File:** `static/sw.js` (Service Worker)

```javascript
/**
 * SKAJLA Service Worker
 * Enables offline support, push notifications, and caching
 */

const CACHE_VERSION = 'skaila-v1.0.0';
const CACHE_STATIC = `${CACHE_VERSION}-static`;
const CACHE_DYNAMIC = `${CACHE_VERSION}-dynamic`;
const CACHE_IMMUTABLE = `${CACHE_VERSION}-immutable`;

// Files to cache immediately on install
const STATIC_ASSETS = [
    '/',
    '/static/css/tokens.css',
    '/static/css/dashboard-premium.css',
    '/static/js/telemetry-tracker.js',
    '/offline.html', // Offline fallback page
    '/static/images/logo.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_STATIC)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then(keys => {
                return Promise.all(
                    keys.filter(key => key.startsWith('skaila-') && key !== CACHE_VERSION)
                        .map(key => caches.delete(key))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - cache-first strategy
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // API requests - network first, cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }
    
    // Static assets - cache first
    if (request.destination === 'style' || request.destination === 'script' || request.destination === 'image') {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }
    
    // Default - network first with offline fallback
    event.respondWith(networkFirstWithOfflineFallback(request));
});

// Push notification event
self.addEventListener('push', (event) => {
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/static/images/logo-192.png',
        badge: '/static/images/badge-72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/',
            timestamp: Date.now()
        },
        actions: [
            {action: 'open', title: 'Apri'},
            {action: 'dismiss', title: 'Chiudi'}
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open') {
        const urlToOpen = event.notification.data.url;
        event.waitUntil(
            clients.openWindow(urlToOpen)
        );
    }
});

// Background sync event (for offline actions)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-telemetry') {
        event.waitUntil(syncTelemetryData());
    }
});

// Helper functions
async function cacheFirstStrategy(request) {
    const cached = await caches.match(request);
    if (cached) return cached;
    
    const response = await fetch(request);
    const cache = await caches.open(CACHE_STATIC);
    cache.put(request, response.clone());
    return response;
}

async function networkFirstStrategy(request) {
    try {
        const response = await fetch(request);
        const cache = await caches.open(CACHE_DYNAMIC);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        if (cached) return cached;
        throw error;
    }
}

async function networkFirstWithOfflineFallback(request) {
    try {
        return await fetch(request);
    } catch (error) {
        const cached = await caches.match(request);
        if (cached) return cached;
        
        // Return offline page
        return caches.match('/offline.html');
    }
}

async function syncTelemetryData() {
    // Get queued telemetry events from IndexedDB
    const db = await openIndexedDB();
    const events = await db.getAll('telemetry-queue');
    
    // Send to server
    for (const event of events) {
        try {
            await fetch('/api/telemetry/events/batch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({events: [event]})
            });
            await db.delete('telemetry-queue', event.id);
        } catch (error) {
            console.error('Sync failed:', error);
        }
    }
}
```

**New File:** `static/manifest.json` (PWA Manifest)

```json
{
    "name": "SKAJLA - Piattaforma Educativa",
    "short_name": "SKAJLA",
    "description": "La tua scuola digitale: registro, AI coach, gamification",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#003B73",
    "theme_color": "#003B73",
    "orientation": "portrait-primary",
    "icons": [
        {
            "src": "/static/images/logo-72.png",
            "sizes": "72x72",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/static/images/logo-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any"
        },
        {
            "src": "/static/images/logo-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ],
    "shortcuts": [
        {
            "name": "Dashboard",
            "short_name": "Home",
            "url": "/dashboard",
            "icons": [{"src": "/static/images/shortcut-home.png", "sizes": "96x96"}]
        },
        {
            "name": "Chat",
            "url": "/chat",
            "icons": [{"src": "/static/images/shortcut-chat.png", "sizes": "96x96"}]
        },
        {
            "name": "AI Coach",
            "url": "/ai-chat",
            "icons": [{"src": "/static/images/shortcut-ai.png", "sizes": "96x96"}]
        }
    ],
    "categories": ["education", "productivity"],
    "screenshots": [
        {
            "src": "/static/images/screenshot-mobile-1.png",
            "sizes": "540x720",
            "type": "image/png"
        }
    ]
}
```

---

#### 2.2 TikTok-Style Vertical Feed

**New Component:** `templates/components/vertical_feed.html`

```html
<!-- Vertical Feed Container (TikTok-like) -->
<div class="vertical-feed-container" id="verticalFeed">
    <div class="feed-controls">
        <button class="feed-filter" data-filter="all">
            <i class="fas fa-globe"></i> Tutto
        </button>
        <button class="feed-filter" data-filter="lessons">
            <i class="fas fa-chalkboard-teacher"></i> Lezioni
        </button>
        <button class="feed-filter" data-filter="quizzes">
            <i class="fas fa-question-circle"></i> Quiz
        </button>
        <button class="feed-filter active" data-filter="my-subject">
            <i class="fas fa-book"></i> Mie Materie
        </button>
    </div>
    
    <div class="feed-scroll-area">
        <!-- Feed items loaded dynamically -->
        <div class="feed-item" data-item-id="1" data-type="video">
            <!-- Video Card -->
            <div class="feed-card video-card">
                <video class="feed-video" playsinline preload="metadata">
                    <source src="/media/lessons/matematica-01.mp4" type="video/mp4">
                </video>
                
                <!-- Video Controls Overlay -->
                <div class="video-overlay">
                    <button class="play-pause-btn">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
                
                <!-- Video Info -->
                <div class="video-info">
                    <h3 class="video-title">Equazioni di Secondo Grado</h3>
                    <p class="video-description">
                        <i class="fas fa-book"></i> Matematica • Prof. Rossi
                    </p>
                    <div class="video-stats">
                        <span><i class="fas fa-eye"></i> 1.2k</span>
                        <span><i class="fas fa-heart"></i> 234</span>
                        <span><i class="fas fa-clock"></i> 45s</span>
                    </div>
                </div>
                
                <!-- Side Actions (TikTok-style) -->
                <div class="side-actions">
                    <button class="action-btn like-btn">
                        <i class="far fa-heart"></i>
                        <span>234</span>
                    </button>
                    <button class="action-btn share-btn">
                        <i class="fas fa-share"></i>
                        <span>Condividi</span>
                    </button>
                    <button class="action-btn save-btn">
                        <i class="far fa-bookmark"></i>
                        <span>Salva</span>
                    </button>
                    <button class="action-btn quiz-btn" data-quiz-id="123">
                        <i class="fas fa-brain"></i>
                        <span>Quiz</span>
                    </button>
                </div>
                
                <!-- Progress Bar -->
                <div class="video-progress">
                    <div class="progress-fill" style="width: 0%;"></div>
                </div>
            </div>
        </div>
        
        <!-- More feed items loaded via infinite scroll -->
    </div>
    
    <!-- Loading Spinner -->
    <div class="feed-loader" style="display: none;">
        <div class="spinner"></div>
        <p>Caricamento contenuti...</p>
    </div>
</div>
```

**New CSS:** `static/css/vertical-feed.css`

```css
/* TikTok-Style Vertical Feed */
.vertical-feed-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #000;
    z-index: 1000;
    overflow: hidden;
}

.feed-controls {
    position: fixed;
    top: 1rem;
    left: 0;
    right: 0;
    z-index: 10;
    display: flex;
    gap: 0.5rem;
    padding: 0 1rem;
    overflow-x: auto;
}

.feed-filter {
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    border: none;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.875rem;
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.2s;
}

.feed-filter.active {
    background: white;
    color: #003B73;
}

.feed-scroll-area {
    width: 100%;
    height: 100%;
    overflow-y: scroll;
    scroll-snap-type: y mandatory;
    -webkit-overflow-scrolling: touch;
}

.feed-item {
    width: 100%;
    height: 100vh;
    scroll-snap-align: start;
    scroll-snap-stop: always;
    position: relative;
}

.feed-card {
    width: 100%;
    height: 100%;
    position: relative;
}

.feed-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.video-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.3);
    opacity: 0;
    transition: opacity 0.3s;
}

.feed-card.paused .video-overlay {
    opacity: 1;
}

.play-pause-btn {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.9);
    border: none;
    color: #003B73;
    font-size: 2rem;
    cursor: pointer;
}

.video-info {
    position: absolute;
    bottom: 6rem;
    left: 1rem;
    right: 5rem;
    color: white;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
}

.video-title {
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.video-description {
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
}

.video-stats {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
}

.side-actions {
    position: absolute;
    right: 1rem;
    bottom: 6rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 1.75rem;
    transition: transform 0.2s;
}

.action-btn:active {
    transform: scale(1.2);
}

.action-btn.liked {
    color: #ff2d55;
}

.action-btn span {
    font-size: 0.75rem;
    margin-top: 0.25rem;
}

.video-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: rgba(255, 255, 255, 0.3);
}

.progress-fill {
    height: 100%;
    background: var(--color-gold-400);
    transition: width 0.1s linear;
}
```

**New JavaScript:** `static/js/vertical-feed.js`

```javascript
/**
 * SKAJLA Vertical Feed (TikTok-like)
 * Infinite scroll, auto-play, swipe gestures
 */

class VerticalFeed {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scrollArea = this.container.querySelector('.feed-scroll-area');
        this.currentIndex = 0;
        this.items = [];
        this.observer = null;
        
        this.init();
    }
    
    async init() {
        // Load initial feed items
        await this.loadFeedItems();
        
        // Setup intersection observer for auto-play
        this.setupIntersectionObserver();
        
        // Setup infinite scroll
        this.setupInfiniteScroll();
        
        // Setup swipe gestures
        this.setupSwipeGestures();
        
        // Setup action buttons
        this.setupActionButtons();
    }
    
    async loadFeedItems(page = 1) {
        try {
            const response = await fetch(`/api/feed/items?page=${page}&per_page=5`);
            const data = await response.json();
            
            data.items.forEach(item => {
                const feedItem = this.createFeedItem(item);
                this.scrollArea.appendChild(feedItem);
                this.items.push(feedItem);
            });
            
            return data.items.length > 0;
        } catch (error) {
            console.error('Feed load error:', error);
            return false;
        }
    }
    
    createFeedItem(itemData) {
        const div = document.createElement('div');
        div.className = 'feed-item';
        div.dataset.itemId = itemData.id;
        div.dataset.type = itemData.type;
        
        if (itemData.type === 'video') {
            div.innerHTML = `
                <div class="feed-card video-card">
                    <video class="feed-video" playsinline preload="metadata" loop>
                        <source src="${itemData.video_url}" type="video/mp4">
                    </video>
                    <div class="video-overlay">
                        <button class="play-pause-btn">
                            <i class="fas fa-play"></i>
                        </button>
                    </div>
                    <div class="video-info">
                        <h3 class="video-title">${itemData.title}</h3>
                        <p class="video-description">
                            <i class="fas fa-book"></i> ${itemData.subject} • ${itemData.teacher}
                        </p>
                        <div class="video-stats">
                            <span><i class="fas fa-eye"></i> ${itemData.views}</span>
                            <span><i class="fas fa-heart"></i> ${itemData.likes}</span>
                            <span><i class="fas fa-clock"></i> ${itemData.duration}s</span>
                        </div>
                    </div>
                    <div class="side-actions">
                        <button class="action-btn like-btn">
                            <i class="far fa-heart"></i>
                            <span>${itemData.likes}</span>
                        </button>
                        <button class="action-btn share-btn">
                            <i class="fas fa-share"></i>
                            <span>Condividi</span>
                        </button>
                        <button class="action-btn save-btn">
                            <i class="far fa-bookmark"></i>
                            <span>Salva</span>
                        </button>
                        ${itemData.quiz_id ? `
                            <button class="action-btn quiz-btn" data-quiz-id="${itemData.quiz_id}">
                                <i class="fas fa-brain"></i>
                                <span>Quiz</span>
                            </button>
                        ` : ''}
                    </div>
                    <div class="video-progress">
                        <div class="progress-fill"></div>
                    </div>
                </div>
            `;
        }
        
        return div;
    }
    
    setupIntersectionObserver() {
        const options = {
            root: this.scrollArea,
            rootMargin: '0px',
            threshold: 0.5 // Video in view when 50% visible
        };
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const video = entry.target.querySelector('.feed-video');
                if (!video) return;
                
                if (entry.isIntersecting) {
                    // Auto-play video
                    video.play().catch(console.error);
                    entry.target.classList.remove('paused');
                    this.startProgressTracking(video);
                } else {
                    // Pause video
                    video.pause();
                    video.currentTime = 0;
                    entry.target.classList.add('paused');
                }
            });
        }, options);
        
        // Observe all feed items
        this.items.forEach(item => this.observer.observe(item));
    }
    
    startProgressTracking(video) {
        const progressBar = video.closest('.feed-card').querySelector('.progress-fill');
        
        video.addEventListener('timeupdate', () => {
            const percentage = (video.currentTime / video.duration) * 100;
            progressBar.style.width = `${percentage}%`;
        });
    }
    
    setupInfiniteScroll() {
        let page = 1;
        let loading = false;
        
        this.scrollArea.addEventListener('scroll', async () => {
            const {scrollTop, scrollHeight, clientHeight} = this.scrollArea;
            
            // Load more when 80% scrolled
            if (scrollTop + clientHeight >= scrollHeight * 0.8 && !loading) {
                loading = true;
                page++;
                const hasMore = await this.loadFeedItems(page);
                loading = false;
                
                if (!hasMore) {
                    // No more items
                    this.scrollArea.removeEventListener('scroll', this);
                }
            }
        });
    }
    
    setupSwipeGestures() {
        let startY = 0;
        let currentY = 0;
        
        this.scrollArea.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
        });
        
        this.scrollArea.addEventListener('touchmove', (e) => {
            currentY = e.touches[0].clientY;
        });
        
        this.scrollArea.addEventListener('touchend', () => {
            const diff = startY - currentY;
            
            // Swipe up (next video)
            if (diff > 50) {
                this.scrollToNext();
            }
            // Swipe down (previous video)
            else if (diff < -50) {
                this.scrollToPrevious();
            }
        });
    }
    
    scrollToNext() {
        if (this.currentIndex < this.items.length - 1) {
            this.currentIndex++;
            this.items[this.currentIndex].scrollIntoView({behavior: 'smooth'});
        }
    }
    
    scrollToPrevious() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.items[this.currentIndex].scrollIntoView({behavior: 'smooth'});
        }
    }
    
    setupActionButtons() {
        // Like button
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.like-btn')) {
                const btn = e.target.closest('.like-btn');
                const itemId = btn.closest('.feed-item').dataset.itemId;
                this.toggleLike(itemId, btn);
            }
        });
        
        // Share button
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.share-btn')) {
                const itemId = e.target.closest('.feed-item').dataset.itemId;
                this.shareContent(itemId);
            }
        });
        
        // Quiz button
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.quiz-btn')) {
                const btn = e.target.closest('.quiz-btn');
                const quizId = btn.dataset.quizId;
                window.location.href = `/quiz/${quizId}`;
            }
        });
    }
    
    async toggleLike(itemId, btn) {
        try {
            const response = await fetch(`/api/feed/items/${itemId}/like`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.liked) {
                btn.classList.add('liked');
                btn.querySelector('i').className = 'fas fa-heart';
            } else {
                btn.classList.remove('liked');
                btn.querySelector('i').className = 'far fa-heart';
            }
            
            btn.querySelector('span').textContent = data.likes;
        } catch (error) {
            console.error('Like error:', error);
        }
    }
    
    async shareContent(itemId) {
        const shareData = {
            title: 'SKAJLA - Contenuto educativo',
            text: 'Guarda questa lezione su SKAJLA!',
            url: `${window.location.origin}/feed/${itemId}`
        };
        
        if (navigator.share) {
            try {
                await navigator.share(shareData);
            } catch (error) {
                console.error('Share error:', error);
            }
        } else {
            // Fallback: Copy link
            navigator.clipboard.writeText(shareData.url);
            alert('Link copiato!');
        }
    }
}

// Initialize feed
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('verticalFeed')) {
        new VerticalFeed('verticalFeed');
    }
});
```

---

#### 2.3 Push Notifications System

**New Route:** `routes/push_notifications_routes.py`

```python
from flask import Blueprint, request, jsonify
from pywebpush import webpush, WebPushException
import json

push_bp = Blueprint('push', __name__, url_prefix='/api/push')

@push_bp.route('/subscribe', methods=['POST'])
@require_login
def subscribe_to_push():
    """Subscribe user to push notifications"""
    subscription_info = request.json
    user_id = session.get('user_id')
    
    # Store subscription in database
    db_manager.execute('''
        INSERT INTO push_subscriptions (
            user_id, endpoint, p256dh, auth, created_at
        ) VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (endpoint) DO UPDATE
        SET user_id = EXCLUDED.user_id,
            p256dh = EXCLUDED.p256dh,
            auth = EXCLUDED.auth
    ''', (
        user_id,
        subscription_info['endpoint'],
        subscription_info['keys']['p256dh'],
        subscription_info['keys']['auth']
    ))
    
    return jsonify({"success": True})

def send_push_notification(user_id: int, title: str, body: str, url: str = '/'):
    """Send push notification to user"""
    # Get user's subscriptions
    subscriptions = db_manager.query('''
        SELECT endpoint, p256dh, auth
        FROM push_subscriptions
        WHERE user_id = %s AND active = TRUE
    ''', (user_id,))
    
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub['endpoint'],
                    'keys': {
                        'p256dh': sub['p256dh'],
                        'auth': sub['auth']
                    }
                },
                data=json.dumps({
                    'title': title,
                    'body': body,
                    'url': url
                }),
                vapid_private_key=os.getenv('VAPID_PRIVATE_KEY'),
                vapid_claims={
                    "sub": "mailto:admin@skaila.app"
                }
            )
        except WebPushException as e:
            print(f"Push failed: {e}")
            # Mark subscription as inactive if expired
            if e.response and e.response.status_code == 410:
                db_manager.execute('''
                    UPDATE push_subscriptions
                    SET active = FALSE
                    WHERE endpoint = %s
                ''', (sub['endpoint'],))
```

**Frontend Push Registration:** `static/js/push-notifications.js`

```javascript
/**
 * Push Notifications Setup
 */

async function registerPushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push notifications not supported');
        return;
    }
    
    try {
        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            console.log('Push permission denied');
            return;
        }
        
        // Get service worker registration
        const registration = await navigator.serviceWorker.ready;
        
        // Subscribe to push
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        });
        
        // Send subscription to server
        await fetch('/api/push/subscribe', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(subscription.toJSON())
        });
        
        console.log('✅ Push notifications enabled');
    } catch (error) {
        console.error('Push registration failed:', error);
    }
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Auto-register on page load
if (window.userLoggedIn) {
    registerPushNotifications();
}
```

---

### Implementation Roadmap: Feature #2

**Phase 1: PWA Foundation (Week 1-2)**
- ✅ Create Service Worker (`sw.js`)
- ✅ Create Web App Manifest (`manifest.json`)
- ✅ Add icons and splash screens
- ✅ Implement offline page

**Phase 2: Vertical Feed (Week 3-4)**
- ✅ Create vertical feed component
- ✅ Implement auto-play and swipe gestures
- ✅ Build infinite scroll
- ✅ Add like/share/save actions

**Phase 3: Content Creation System (Week 5-6)**
- ✅ Teacher video upload tool (max 60s)
- ✅ Video compression pipeline
- ✅ Quiz integration with videos
- ✅ Content moderation

**Phase 4: Push Notifications (Week 7)**
- ✅ Setup VAPID keys
- ✅ Implement push subscription
- ✅ Integrate with alert system
- ✅ Create notification templates

**Phase 5: Gamification Integration (Week 8)**
- ✅ Streaks for daily app opens
- ✅ Badges for feed engagement
- ✅ XP for watching educational content
- ✅ Leaderboard for most engaged

---

## 📄 KILLER FEATURE #3: Compliance & Paperless Engine

### Problem Statement

**Competitors still use PAPER:**
- ClasseViva: PCTO forms must be printed and signed
- WeSchool: Parent authorizations via email PDF
- Both: no digital timestamping, no legal validity

**Our Solution:** **100% Digital Validation Workflow** with e-signatures and blockchain timestamping

---

### Architecture Design

#### 3.1 Database Schema Changes

```sql
-- Digital Documents Table
CREATE TABLE digital_documents (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,
    -- Types: 'pcto_agreement', 'parent_authorization', 'field_trip_consent',
    --        'grade_appeal', 'absence_justification', 'medical_certificate'
    
    title VARCHAR(200),
    description TEXT,
    
    -- Document metadata
    created_by INTEGER REFERENCES utenti(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scuola_id INTEGER REFERENCES scuole(id),
    
    -- Document content (PDF generated from template)
    pdf_url TEXT,
    template_id INTEGER REFERENCES document_templates(id),
    template_data JSONB, -- Data used to fill template
    
    -- Status workflow
    status VARCHAR(50) DEFAULT 'draft',
    -- 'draft', 'pending_signature', 'partially_signed', 'fully_signed', 
    -- 'rejected', 'expired', 'archived'
    
    -- Blockchain timestamping
    blockchain_hash VARCHAR(64), -- SHA-256 hash of document
    blockchain_timestamp TIMESTAMP,
    blockchain_tx_id VARCHAR(100), -- Transaction ID on blockchain (if used)
    
    -- Legal validity
    legally_valid BOOLEAN DEFAULT FALSE,
    validation_method VARCHAR(50), -- 'digital_signature', 'otp_verification', 'spid'
    
    -- Expiration
    expires_at TIMESTAMP,
    
    -- Security
    access_code VARCHAR(10), -- Optional PIN for viewing
    encrypted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_doc_type_status (document_type, status),
    INDEX idx_doc_created (created_by, created_at DESC),
    INDEX idx_doc_school (scuola_id, created_at DESC)
);

-- Digital Signatures Table
CREATE TABLE digital_signatures (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES digital_documents(id) ON DELETE CASCADE,
    
    -- Signer info
    signer_user_id INTEGER REFERENCES utenti(id), -- If registered user
    signer_name VARCHAR(200), -- For external signers (parents not registered)
    signer_email VARCHAR(200),
    signer_role VARCHAR(50), -- 'student', 'parent', 'teacher', 'principal', 'company_rep'
    
    -- Signature metadata
    signature_method VARCHAR(50),
    -- 'otp_email', 'otp_sms', 'spid', 'cie', 'drawn_signature', 'typed_acceptance'
    
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    geolocation JSONB, -- {lat, lon, city} if available
    
    -- OTP verification (if used)
    otp_code VARCHAR(6),
    otp_verified_at TIMESTAMP,
    otp_attempts INTEGER DEFAULT 0,
    
    -- Signature image (if drawn)
    signature_image_url TEXT,
    
    -- Legal validity
    legally_binding BOOLEAN DEFAULT TRUE,
    signature_hash VARCHAR(64), -- Hash of signature data for integrity
    
    -- Revocation (if signature needs to be invalidated)
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,
    
    INDEX idx_sig_document (document_id, signed_at),
    INDEX idx_sig_user (signer_user_id, signed_at DESC),
    INDEX idx_sig_email (signer_email)
);

-- Document Templates Table
CREATE TABLE document_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100),
    template_type VARCHAR(50), -- 'pcto', 'authorization', 'consent', 'appeal'
    
    -- Template structure
    html_template TEXT, -- HTML template with placeholders
    required_fields JSONB, -- Array of required fields
    -- Example: [
    --   {"field": "student_name", "type": "text", "label": "Nome Studente"},
    --   {"field": "company_name", "type": "text", "label": "Nome Azienda"},
    --   {"field": "start_date", "type": "date", "label": "Data Inizio"}
    -- ]
    
    -- Signature requirements
    required_signatures JSONB,
    -- Example: [
    --   {"role": "student", "label": "Firma Studente"},
    --   {"role": "parent", "label": "Firma Genitore"},
    --   {"role": "company_rep", "label": "Firma Tutor Aziendale"}
    -- ]
    
    -- Metadata
    created_by INTEGER REFERENCES utenti(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_template_type (template_type, active)
);

-- PCTO (Internship) Management Table
CREATE TABLE pcto_agreements (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES utenti(id),
    scuola_id INTEGER REFERENCES scuole(id),
    
    -- Company info
    company_name VARCHAR(200),
    company_vat VARCHAR(20),
    company_address TEXT,
    company_email VARCHAR(200),
    company_phone VARCHAR(20),
    
    -- Tutor info
    school_tutor_id INTEGER REFERENCES utenti(id), -- Teacher supervising
    company_tutor_name VARCHAR(200),
    company_tutor_email VARCHAR(200),
    company_tutor_phone VARCHAR(20),
    
    -- Period
    start_date DATE,
    end_date DATE,
    total_hours INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'awaiting_signatures', 'active', 'completed', 'cancelled'
    
    -- Document reference
    agreement_document_id INTEGER REFERENCES digital_documents(id),
    
    -- Progress tracking
    hours_completed INTEGER DEFAULT 0,
    attendance_log JSONB, -- Daily attendance records
    
    -- Final evaluation
    final_grade DECIMAL(4,2),
    school_evaluation JSONB,
    company_evaluation JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    INDEX idx_pcto_student (student_id, status),
    INDEX idx_pcto_school (scuola_id, start_date DESC)
);

-- Audit Log for Document Actions
CREATE TABLE document_audit_log (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES digital_documents(id) ON DELETE CASCADE,
    
    action VARCHAR(50),
    -- 'created', 'viewed', 'downloaded', 'signed', 'rejected', 'deleted', 'modified'
    
    performed_by INTEGER REFERENCES utenti(id),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    
    details JSONB, -- Additional action details
    
    INDEX idx_audit_document (document_id, performed_at DESC),
    INDEX idx_audit_user (performed_by, performed_at DESC)
);
```

---

#### 3.2 Backend Service: Digital Document Engine

**New Module:** `services/documents/digital_document_engine.py`

```python
"""
SKAJLA Digital Document Engine
100% Paperless workflow with e-signatures and blockchain timestamping
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import secrets
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode

class DigitalDocumentEngine:
    """
    Handles creation, signing, and validation of digital documents
    """
    
    def create_document(
        self,
        document_type: str,
        template_id: int,
        template_data: Dict[str, Any],
        created_by: int,
        scuola_id: int
    ) -> int:
        """
        Create a new digital document from template
        
        Returns:
            document_id
        """
        # Get template
        template = db_manager.query('''
            SELECT * FROM document_templates
            WHERE id = %s AND active = TRUE
        ''', (template_id,), one=True)
        
        if not template:
            raise ValueError("Template not found or inactive")
        
        # Validate required fields
        required_fields = json.loads(template['required_fields'])
        for field in required_fields:
            if field['field'] not in template_data:
                raise ValueError(f"Missing required field: {field['label']}")
        
        # Generate PDF from template
        pdf_url = self._generate_pdf_from_template(
            template['html_template'],
            template_data
        )
        
        # Calculate document hash
        doc_hash = self._calculate_document_hash(pdf_url, template_data)
        
        # Create document record
        document_id = db_manager.execute('''
            INSERT INTO digital_documents (
                document_type, title, created_by, scuola_id,
                pdf_url, template_id, template_data,
                blockchain_hash, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            document_type,
            template_data.get('title', f'{document_type.replace("_", " ").title()}'),
            created_by,
            scuola_id,
            pdf_url,
            template_id,
            json.dumps(template_data),
            doc_hash,
            'draft'
        ), returning=True)['id']
        
        # Timestamp on blockchain (if enabled)
        if os.getenv('BLOCKCHAIN_ENABLED') == 'true':
            self._timestamp_on_blockchain(document_id, doc_hash)
        
        # Audit log
        self._log_audit_action(document_id, 'created', created_by)
        
        return document_id
    
    def request_signatures(
        self,
        document_id: int,
        signers: List[Dict[str, Any]]
    ):
        """
        Request digital signatures from specified signers
        
        Args:
            signers: List of signer info
                [
                    {"role": "parent", "email": "parent@example.com", "name": "Mario Rossi"},
                    {"role": "student", "user_id": 123}
                ]
        """
        # Update document status
        db_manager.execute('''
            UPDATE digital_documents
            SET status = 'pending_signature'
            WHERE id = %s
        ''', (document_id,))
        
        # Send signature requests
        for signer in signers:
            # Generate unique access code
            access_code = secrets.token_urlsafe(8)
            
            # Create signature placeholder
            db_manager.execute('''
                INSERT INTO digital_signatures (
                    document_id, signer_role, signer_email, signer_name,
                    signer_user_id, otp_code, signature_method
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                document_id,
                signer['role'],
                signer.get('email'),
                signer.get('name'),
                signer.get('user_id'),
                access_code,
                'otp_email'
            ))
            
            # Send email with signature link
            self._send_signature_request_email(
                document_id=document_id,
                signer_email=signer['email'],
                signer_name=signer['name'],
                access_code=access_code
            )
    
    def sign_document(
        self,
        document_id: int,
        signer_user_id: Optional[int],
        signer_email: str,
        signature_method: str,
        signature_data: Dict[str, Any],
        ip_address: str,
        user_agent: str
    ) -> bool:
        """
        Sign a digital document
        
        Args:
            signature_data: Contains OTP code, drawn signature image, etc.
        
        Returns:
            True if signature successful
        """
        # Get document
        document = db_manager.query('''
            SELECT * FROM digital_documents WHERE id = %s
        ''', (document_id,), one=True)
        
        if not document or document['status'] not in ['pending_signature', 'partially_signed']:
            raise ValueError("Document cannot be signed in current status")
        
        # Verify OTP if using email/sms method
        if signature_method in ['otp_email', 'otp_sms']:
            otp_code = signature_data.get('otp_code')
            if not self._verify_otp(document_id, signer_email, otp_code):
                return False
        
        # Process signature image if drawn
        signature_image_url = None
        if signature_method == 'drawn_signature':
            signature_image_url = self._save_signature_image(
                signature_data['image_data']
            )
        
        # Calculate signature hash
        signature_hash = self._calculate_signature_hash(signature_data)
        
        # Create signature record
        db_manager.execute('''
            UPDATE digital_signatures
            SET 
                signer_user_id = %s,
                signature_method = %s,
                signed_at = NOW(),
                ip_address = %s,
                user_agent = %s,
                signature_image_url = %s,
                signature_hash = %s,
                legally_binding = TRUE
            WHERE document_id = %s AND signer_email = %s
        ''', (
            signer_user_id,
            signature_method,
            ip_address,
            user_agent,
            signature_image_url,
            signature_hash,
            document_id,
            signer_email
        ))
        
        # Check if all required signatures collected
        if self._check_all_signatures_complete(document_id):
            db_manager.execute('''
                UPDATE digital_documents
                SET 
                    status = 'fully_signed',
                    legally_valid = TRUE
                WHERE id = %s
            ''', (document_id,))
            
            # Notify creator document is fully signed
            self._notify_document_fully_signed(document_id)
        else:
            db_manager.execute('''
                UPDATE digital_documents
                SET status = 'partially_signed'
                WHERE id = %s
            ''', (document_id,))
        
        # Audit log
        self._log_audit_action(document_id, 'signed', signer_user_id or 0, {
            'signer_email': signer_email,
            'method': signature_method
        })
        
        return True
    
    def _calculate_document_hash(self, pdf_url: str, template_data: Dict) -> str:
        """Calculate SHA-256 hash of document for blockchain timestamping"""
        hasher = hashlib.sha256()
        
        # Hash PDF content
        with open(pdf_url, 'rb') as f:
            hasher.update(f.read())
        
        # Hash template data
        hasher.update(json.dumps(template_data, sort_keys=True).encode())
        
        return hasher.hexdigest()
    
    def _timestamp_on_blockchain(self, document_id: int, doc_hash: str):
        """
        Timestamp document hash on blockchain for immutable proof
        
        Note: This is a simplified version. In production, use a service like
        OpenTimestamps, Ethereum, or a custom blockchain solution.
        """
        # Placeholder for blockchain integration
        # In real implementation:
        # 1. Send hash to blockchain service
        # 2. Get transaction ID
        # 3. Store tx_id in database
        
        tx_id = f"blockchain_tx_{secrets.token_hex(16)}"
        timestamp = datetime.utcnow()
        
        db_manager.execute('''
            UPDATE digital_documents
            SET 
                blockchain_timestamp = %s,
                blockchain_tx_id = %s
            WHERE id = %s
        ''', (timestamp, tx_id, document_id))
    
    def _verify_otp(self, document_id: int, email: str, otp_code: str) -> bool:
        """Verify OTP code for signature"""
        signature = db_manager.query('''
            SELECT * FROM digital_signatures
            WHERE document_id = %s AND signer_email = %s
        ''', (document_id, email), one=True)
        
        if not signature:
            return False
        
        # Check OTP code
        if signature['otp_code'] != otp_code:
            # Increment attempt counter
            db_manager.execute('''
                UPDATE digital_signatures
                SET otp_attempts = otp_attempts + 1
                WHERE id = %s
            ''', (signature['id'],))
            
            # Block after 3 attempts
            if signature['otp_attempts'] >= 2:
                raise ValueError("Too many OTP attempts. Please request a new code.")
            
            return False
        
        # Mark OTP as verified
        db_manager.execute('''
            UPDATE digital_signatures
            SET otp_verified_at = NOW()
            WHERE id = %s
        ''', (signature['id'],))
        
        return True
    
    def _check_all_signatures_complete(self, document_id: int) -> bool:
        """Check if all required signatures are collected"""
        # Get template required signatures
        document = db_manager.query('''
            SELECT dt.required_signatures
            FROM digital_documents dd
            JOIN document_templates dt ON dd.template_id = dt.id
            WHERE dd.id = %s
        ''', (document_id,), one=True)
        
        required_sigs = json.loads(document['required_signatures'])
        required_roles = [sig['role'] for sig in required_sigs]
        
        # Get collected signatures
        collected_sigs = db_manager.query('''
            SELECT DISTINCT signer_role
            FROM digital_signatures
            WHERE document_id = %s AND signed_at IS NOT NULL
        ''', (document_id,))
        
        collected_roles = [sig['signer_role'] for sig in collected_sigs]
        
        # Check if all required roles signed
        return set(required_roles).issubset(set(collected_roles))
    
    def create_pcto_agreement(
        self,
        student_id: int,
        company_data: Dict[str, Any],
        tutor_data: Dict[str, Any],
        period_data: Dict[str, Any]
    ) -> int:
        """
        Create PCTO (internship) agreement with digital signatures
        
        Returns:
            pcto_agreement_id
        """
        # Get student info
        student = db_manager.query('''
            SELECT * FROM utenti WHERE id = %s
        ''', (student_id,), one=True)
        
        # Create digital document for agreement
        template_data = {
            'title': f'Convenzione PCTO - {student["nome"]} {student["cognome"]}',
            'student_name': f'{student["nome"]} {student["cognome"]}',
            'student_birth_date': student.get('data_nascita'),
            'student_fiscal_code': student.get('codice_fiscale'),
            'company_name': company_data['name'],
            'company_vat': company_data['vat'],
            'company_address': company_data['address'],
            'school_tutor_name': tutor_data['school_tutor_name'],
            'company_tutor_name': tutor_data['company_tutor_name'],
            'start_date': period_data['start_date'],
            'end_date': period_data['end_date'],
            'total_hours': period_data['total_hours']
        }
        
        # Create document
        document_id = self.create_document(
            document_type='pcto_agreement',
            template_id=self._get_pcto_template_id(),
            template_data=template_data,
            created_by=student_id,
            scuola_id=student['scuola_id']
        )
        
        # Create PCTO agreement record
        pcto_id = db_manager.execute('''
            INSERT INTO pcto_agreements (
                student_id, scuola_id, company_name, company_vat,
                company_address, company_email, company_phone,
                school_tutor_id, company_tutor_name, company_tutor_email,
                start_date, end_date, total_hours,
                agreement_document_id, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            student_id,
            student['scuola_id'],
            company_data['name'],
            company_data['vat'],
            company_data['address'],
            company_data['email'],
            company_data['phone'],
            tutor_data['school_tutor_id'],
            tutor_data['company_tutor_name'],
            tutor_data['company_tutor_email'],
            period_data['start_date'],
            period_data['end_date'],
            period_data['total_hours'],
            document_id,
            'awaiting_signatures'
        ), returning=True)['id']
        
        # Request signatures
        self.request_signatures(document_id, [
            {
                'role': 'student',
                'user_id': student_id,
                'email': student['email'],
                'name': f'{student["nome"]} {student["cognome"]}'
            },
            {
                'role': 'parent',
                'email': student.get('parent_email'),
                'name': student.get('parent_name')
            },
            {
                'role': 'company_rep',
                'email': tutor_data['company_tutor_email'],
                'name': tutor_data['company_tutor_name']
            },
            {
                'role': 'school_tutor',
                'user_id': tutor_data['school_tutor_id']
            }
        ])
        
        return pcto_id

# Global instance
document_engine = DigitalDocumentEngine()
```

---

### Implementation Roadmap: Feature #3

**Phase 1: Document Templates (Week 1-2)**
- ✅ Create template system
- ✅ Build PCTO agreement template
- ✅ Build parent authorization templates
- ✅ PDF generation engine

**Phase 2: E-Signature System (Week 3-4)**
- ✅ OTP verification (email/SMS)
- ✅ Drawn signature capture
- ✅ Digital signature storage

**Phase 3: Blockchain Timestamping (Week 5)**
- ✅ Integrate OpenTimestamps or custom solution
- ✅ Document hash calculation
- ✅ Verification UI

**Phase 4: PCTO Management (Week 6-7)**
- ✅ PCTO agreement workflow
- ✅ Progress tracking dashboard
- ✅ Attendance logging
- ✅ Final evaluation forms

**Phase 5: Audit & Compliance (Week 8)**
- ✅ Audit log viewer for admins
- ✅ Legal validity verification
- ✅ Export for regulatory compliance

---

## 🚢 Deployment & Rollout Strategy

### Technical Requirements

**Infrastructure:**
- Upgrade to PostgreSQL 15+ for JSONB performance
- Setup Redis for real-time features
- CDN for video delivery (CloudFlare/AWS CloudFront)
- VAPID keys generation for push notifications
- SSL certificates (Let's Encrypt)

**Third-Party Services:**
- OpenTimestamps (blockchain timestamping)
- Twilio (SMS OTP)
- AWS S3/Replit Object Storage (file storage)
- FFmpeg (video compression)

### Rollout Phases

**Phase 1: Beta Testing (2 months)**
- Select 3 pilot schools
- Deploy Feature #1 (Telemetry + Early Warning)
- Collect teacher feedback
- Tune AI algorithms

**Phase 2: PWA Launch (1 month)**
- Deploy Feature #2 (Mobile-First PWA)
- Marketing campaign targeting Gen-Z students
- Monitor engagement metrics

**Phase 3: Paperless Compliance (1 month)**
- Deploy Feature #3 (Digital Documents)
- Legal validation with schools
- Training for admin staff

**Phase 4: General Availability (Ongoing)**
- Open to all schools
- Continuous monitoring and optimization

---

## 📊 Success Metrics

### Feature #1: Smart AI-Tutoring
- **Early Warning Accuracy**: >80% of alerts result in intervention
- **Student Recovery Rate**: >70% of students on recovery paths improve
- **Teacher Response Time**: <24h average to acknowledge alerts
- **Prevented Failures**: Track students who would have failed without intervention

### Feature #2: Gen-Z Mobile-First
- **DAU (Daily Active Users)**: Target 60% of students using app daily
- **Session Duration**: >15 min average per session
- **PWA Install Rate**: >40% of mobile users install PWA
- **Video Engagement**: >70% completion rate for educational videos
- **Retention**: >80% 30-day retention

### Feature #3: Paperless Compliance
- **Paper Reduction**: 100% digital PCTO agreements
- **Signature Completion Rate**: >90% within 7 days
- **Time Savings**: <5 min to create and sign vs 2+ days paper process
- **Legal Validity**: Zero rejected documents in audits

---

## 💰 Cost Analysis

**Development Costs:**
- Backend Development (3 engineers × 3 months): €90,000
- Frontend Development (2 engineers × 3 months): €60,000
- DevOps & Infrastructure: €20,000
- QA & Testing: €15,000
**Total Dev**: €185,000

**Ongoing Costs:**
- Infrastructure (CDN, servers, storage): €2,000/month
- Third-party services (Twilio, blockchain): €500/month
- Maintenance (1 engineer part-time): €3,000/month
**Total Monthly**: €5,500

**ROI:**
- Target: 100 schools @ €599/month = €59,900/month
- Break-even: ~4 months post-launch
- Projected Year 1 Revenue: €600,000+

---

## 🎯 Competitive Positioning

### vs ClasseViva
| Feature | ClasseViva | SKAJLA Super-App |
|---------|-----------|------------------|
| Early Warning System | ❌ No | ✅ **AI-powered telemetry** |
| Mobile Experience | ⚠️ Responsive only | ✅ **Native PWA + Vertical Feed** |
| Paperless PCTO | ❌ Print & sign | ✅ **100% digital e-signatures** |
| Student Engagement | 📉 Low (passive) | 📈 **High (gamified TikTok-style)** |
| Pricing | €450/month | **€599/month** (+33% for 3x value) |

### vs WeSchool
| Feature | WeSchool | SKAJLA Super-App |
|---------|----------|------------------|
| Learning Analytics | ⚠️ Basic reports | ✅ **Behavioral telemetry + ML** |
| Content Format | 📄 Documents only | ✅ **Short-form vertical videos** |
| E-Signatures | ❌ No | ✅ **Blockchain-timestamped** |
| UX Design | 😴 Boring | 🚀 **Gen-Z optimized** |

**SKAJLA wins on all 3 fronts:** Prevention, Engagement, Efficiency

---

## 📝 Next Steps

1. **Review & Approve**: CTO and Product team review this document
2. **Kickoff Meeting**: Assemble development team
3. **Sprint Planning**: Break down into 2-week sprints
4. **Pilot School Selection**: Choose 3 schools for beta testing
5. **Development Start**: Begin with Feature #1 (highest impact)

---

**Document Status**: ✅ **Ready for Implementation**  
**Estimated Time to Market**: 6 months  
**Confidence Level**: High (95%)

---

*This architecture document is a living document and will be updated as development progresses.*
