# Overview

SKAILA is a comprehensive educational platform that facilitates communication and learning within school environments. The platform serves as a multi-role messaging system connecting students, teachers, parents, and administrators through a real-time chat interface. It features an intelligent AI chatbot for personalized tutoring, gamification systems to enhance student engagement, and comprehensive analytics for tracking learning progress.

The platform is built as a Flask web application with Socket.IO for real-time communication, supporting scalable user management and educational tools designed specifically for the Italian education system.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask as the primary web framework with a modular architecture pattern. The main application is structured around separate blueprints for authentication, dashboard, and API routes, promoting clean separation of concerns and maintainability.

## Database Layer
The system implements a flexible database architecture with support for both SQLite (development) and PostgreSQL (production). A custom DatabaseManager class handles connection pooling and provides fallback mechanisms, ensuring scalability for 1000+ concurrent users. The database schema includes comprehensive tables for users, chat rooms, messages, gamification data, AI interaction tracking, and **multi-tenant school management**.

## Multi-Tenant School System
**NEW:** SKAILA now features a comprehensive school-class-teacher management system:
- **School Organization**: Multiple schools with unique codes and teacher invite systems
- **Class Management**: Dynamic class creation and automatic student-teacher associations  
- **Role-Based Registration**: Intelligent registration flow that assigns student/teacher roles based on invite codes
- **Automated Group Creation**: System automatically creates school, class, and teacher chat rooms
- **Scalable Architecture**: Supports unlimited schools with isolated data and communication channels

## Real-time Communication
Socket.IO integration enables real-time messaging functionality with automatic reconnection and room-based chat organization. The system supports multiple chat types including class-based, thematic, and administrative channels.

## AI Integration
**MAJOR UPDATE - 100% Native SKAILA AI System (No OpenAI dependency):**
The platform now features a completely native AI tutoring system built specifically for SKAILA:

### SKAILA AI Brain Engine (`skaila_ai_brain.py`)
- **Intelligent Context Analysis**: Analyzes complete student profile (level, XP, streak, class, subject progress)
- **Subject Detection**: Auto-detects subject from student messages using keyword matching
- **Sentiment Analysis**: Identifies student emotional state (frustrated, motivated, curious, confused)
- **Response Prioritization**: Emergency streak, help needed, quiz request, general encouragement
- **8 Response Types**: Personalized responses based on context, performance, and needs

### Adaptive Quiz System (`skaila_quiz_manager.py`)
- **Quiz Database**: 34+ multi-subject quizzes (matematica, italiano, storia, scienze, inglese, geografia)
- **Difficulty Adaptation**: Automatically adjusts difficulty based on student performance history
- **Weak Topic Focus**: 80% probability to serve quizzes on weak topics for targeted improvement
- **XP & Badge Integration**: Awards XP with speed bonuses, unlocks badges, updates leaderboards
- **Subject Progress Tracking**: Real-time accuracy calculation, topic-level analytics

### Social Learning System (`social_learning_system.py`)
- **Peer Help Matching**: Finds expert classmates (75%+ accuracy) for subject-specific help
- **Study Groups**: Create/join subject-based study groups (max 6 members)
- **Collaborative XP**: Awards XP for both helpers and learners
- **Class Integration**: Automatically filters by school and class for relevant peer connections

### Subject Progress Analytics (`subject_progress_analytics.py`)
- **Comprehensive Overview**: Total quizzes, accuracy, XP, level, trend analysis
- **Topic Statistics**: Per-topic performance, avg time, accuracy tracking
- **Weak Area Identification**: Detects topics with <70% accuracy for focused practice
- **Learning Path Generator**: Creates personalized 5-step improvement plans
- **XP History**: 30-day chart showing daily XP and quiz activity
- **AI Suggestions**: Personalized recommendations based on performance patterns

## Gamification Engine
A comprehensive gamification system tracks user engagement through XP points, levels, badges, and achievements. The system includes streak tracking, performance analytics, and reward mechanisms designed to motivate student participation and learning progress.

## Performance Optimization
Multiple performance enhancement systems including:
- Multi-level caching with LRU eviction policies
- Session management with Redis support for scalability
- Performance monitoring for system metrics and response times
- Connection pooling for database operations

## Security Features
The authentication system uses bcrypt for password hashing with fallback support for legacy systems. Rate limiting and attempt tracking prevent brute force attacks, while role-based access control ensures appropriate permissions across different user types.

# External Dependencies

## Core Dependencies
- **Flask**: Web framework for application structure and routing
- **Flask-SocketIO**: Real-time bidirectional communication between clients and server
- **OpenAI API**: Powers the intelligent AI chatbot with natural language processing capabilities
- **bcrypt**: Secure password hashing and verification
- **psutil**: System performance monitoring and resource tracking

## Database Systems
- **SQLite**: Default development database with file-based storage
- **PostgreSQL**: Production database with connection pooling (via psycopg2)
- **Redis**: Optional session storage and caching layer for improved scalability

## Frontend Assets
- **Font Awesome**: Icon library for user interface elements
- **Google Fonts (Inter)**: Typography system for consistent visual design
- **Chart.js**: Data visualization for analytics and gamification dashboards

## Development Tools
- **Gunicorn**: WSGI HTTP server for production deployment
- **python-dotenv**: Environment variable management for configuration
- **eventlet**: Asynchronous networking library for Socket.IO support

# New Features (December 2025)

## Teaching Materials Management System
**Complete file upload system for teachers** (`teaching_materials_manager.py`):
- **File Upload**: PDF, DOC, PPT, images, video, audio support (max 50MB)
- **Organization**: By subject, class, public/private visibility
- **Permissions**: Class-based access control, teacher ownership
- **Download Tracking**: Analytics on material usage and popularity
- **Search**: Advanced search by title, description, subject, teacher
- **Statistics**: Teacher dashboard with upload stats, most downloaded materials

## Electronic Class Register (Registro Elettronico)
**Comprehensive student management system** (`registro_elettronico.py`):

### Attendance Management
- **Daily Tracking**: Present, absent, late, early dismissal status
- **Class-Wide**: Bulk attendance marking for entire class
- **Statistics**: Attendance percentage, absence patterns, late frequency
- **Justifications**: Parent-submitted absence justifications with approval workflow

### Grades Management
- **Grade Recording**: Italian scale (1-10) with type (scritto, orale, pratico)
- **Weighted Averages**: Automatic calculation with customizable weights
- **Subject Analytics**: Per-subject averages, grade distribution, trends
- **Student Reports**: Comprehensive grade history and performance summaries

### Disciplinary Notes
- **Note Recording**: Type, severity (lieve/media/grave), detailed description
- **Teacher Attribution**: Tracks which teacher issued each note
- **Pattern Detection**: Identifies recurring behavior issues

### Lesson Calendar
- **Lesson Planning**: Date, time, topic, homework assignments
- **Material Linking**: Connect lessons with uploaded teaching materials
- **Class History**: Complete lesson log with topics covered and homework given

## AI-Powered Register Intelligence
**Smart analytics for student success** (`ai_registro_intelligence.py`):

### Risk Assessment System
- **Student Risk Score** (0-100): Combines attendance, grades, behavior, trend analysis
- **Risk Levels**: Basso, Medio, Alto, Critico with priority classification
- **Multi-Factor Analysis**: Attendance <75%, multiple failing subjects, disciplinary issues, performance decline
- **Actionable Insights**: Specific recommendations for each risk factor

### Anomaly Detection
- **Grade Drop Detection**: Alerts on >1.5 point average decline
- **Absence Pattern Changes**: Identifies sudden increase in absences
- **Behavioral Changes**: Flags unusual patterns requiring attention

### Intervention Planning
- **Personalized Plans**: Custom action plans based on student needs
- **Timeline**: Specific deadlines and follow-up dates
- **Multi-Stakeholder**: Involves teachers, coordinators, parents, tutors
- **Success Indicators**: Measurable goals for tracking improvement

### Class Health Monitoring
- **Class Health Score** (0-100): Overall class performance metric
- **At-Risk Identification**: Automatically identifies struggling students
- **Trend Analysis**: Tracks class-wide performance patterns
- **Priority Concerns**: Highlights most pressing class-wide issues

## Parent Communication System
**Automated reporting for families** (`parent_reports_generator.py`):

### Weekly Reports
- **Attendance Summary**: Daily presence/absence breakdown
- **New Grades**: All grades received during week
- **Behavior Updates**: Disciplinary notes and incidents
- **Homework Tracking**: Assignments due and completed
- **AI Insights**: Strengths, areas for improvement, recommendations

### Monthly Reports
- **Executive Summary**: Overall status, attendance rate, average grade, behavior score
- **Detailed Analytics**: Subject-by-subject performance breakdown
- **Trend Analysis**: Monthly improvement/decline patterns per subject
- **Risk Assessment**: Complete AI risk analysis and intervention plan
- **Action Plan**: Specific steps for parents and school, follow-up dates

### Real-Time Notifications
- **Immediate Alerts**: New grades, absences, disciplinary notes
- **Priority System**: High/medium/low urgency classification
- **Action Required**: Flags notifications needing parent response
- **Event Types**: Grade updates, absence alerts, excellent performance celebrations

## API Routes for AI System
**RESTful endpoints** (`skaila_ai_routes.py`):
- `POST /api/ai/chat` - AI chatbot conversation with context analysis
- `POST /api/ai/quiz/get` - Get adaptive quiz based on performance
- `POST /api/ai/quiz/submit` - Submit quiz answer with XP calculation
- `GET /api/ai/progress/<subject>` - Subject-specific progress analytics
- `GET /api/ai/leaderboard/<subject>` - Class leaderboard by subject
- `GET /api/ai/stats` - Overall AI interaction and quiz statistics

# Database Schema Updates

## New Tables (Production PostgreSQL)

### AI & Quiz System
- `quiz_bank` - Multi-subject quiz repository with difficulty levels
- `student_quiz_history` - Complete quiz attempt tracking with XP
- `student_subject_progress` - Per-subject analytics and topic tracking
- `ai_learning_context` - Student learning profile and patterns
- `ai_conversations` - AI chatbot interaction history

### Social Learning
- `peer_help_requests` - Peer tutoring request and completion tracking
- `study_groups` - Subject-based collaborative study groups
- `study_group_members` - Group membership and XP tracking

### Teaching Materials
- `teaching_materials` - File metadata, permissions, download tracking
- `material_downloads` - Download history and analytics

### Electronic Register
- `registro_presenze` - Daily attendance with status and notes
- `registro_voti` - Grade recording with weighted averages
- `registro_note_disciplinari` - Disciplinary notes with severity levels
- `registro_assenze_giustificate` - Absence justification workflow
- `registro_calendario_lezioni` - Lesson planning and homework tracking

# Deployment Checklist

## Required Secrets (Add to Replit Secrets)
- `SECRET_KEY` - Flask session encryption (CRITICAL) - **MUST BE ADDED BY USER IN REPLIT SECRETS**
  - Generate a secure random key using: `python -c "import secrets; print(secrets.token_hex(32))"`
  - Add it to Replit Secrets panel before deployment
- `DATABASE_URL` - PostgreSQL connection (auto-provided by Replit)

## Pre-Deployment Tasks
1. ✅ Add SECRET_KEY to Replit Secrets
2. ✅ Verify PostgreSQL database connection
3. ✅ Run quiz population: `python populate_quiz_database.py`
4. ⏳ Test all API endpoints
5. ⏳ Complete frontend integration (GIORNO 7)
6. ⏳ End-to-end testing
7. ⏳ Performance optimization

## Known Issues / TODO
- Email notifications currently simulate (print to console) - needs real SMTP integration
- Frontend web interface for new systems pending (GIORNO 7)
- LSP diagnostics present in new modules (non-blocking, type hints)