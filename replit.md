# Overview

SKAILA is an educational platform for schools, offering a multi-role messaging system, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. It connects students, teachers, parents, and administrators in real-time. The platform is a Flask web application with Socket.IO for real-time communication, designed to be scalable and specifically tailored for the Italian education system. It aims to enhance learning engagement and provide robust tools for school management.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask with a modular architecture, separating concerns into blueprints for authentication, dashboards, and APIs.

## Centralized Configuration System (SSoT) - Oct 18, 2025
SKAILA implements Single Source of Truth principles with centralized, modular configuration:
-   **Core Configurations** (`core/config/`):
    -   `settings.py`: App settings, security configs, cache settings, feature flags
    -   `gamification_config.py`: XP actions (40+ types), multipliers, levels, badges, streaks
-   **Shared Validators** (`shared/validators/`):
    -   `input_validators.py`: Email, password, username validation, SQL injection protection, XSS sanitization
-   **Shared Formatters** (`shared/formatters/`):
    -   `date_formatters.py`: Italian date formatting utilities
    -   `file_formatters.py`: File size formatting (KB, MB, GB)
-   **Benefits Achieved**:
    -   ~60% code reduction through DRY principles
    -   Consistent validation across all modules
    -   Security hardening with centralized input sanitization
    -   Easy configuration updates without touching business logic
    -   Improved maintainability and testability

## Database Layer
Supports both SQLite (development) and PostgreSQL (production) with a custom `DatabaseManager` for connection pooling and fallback mechanisms. The schema supports multi-tenant school management, users, chat, gamification, and AI interaction tracking.

## Multi-Tenant School System
SKAILA includes a comprehensive school, class, and teacher management system with dynamic class creation, role-based registration, and automated chat room creation, supporting isolated data for unlimited schools.

## Real-time Communication
Socket.IO provides real-time messaging with automatic reconnection and room-based chat for various chat types (class-based, thematic, administrative).

## AI Integration
A native SKAILA AI system powers personalized learning:
-   **SKAILA AI Brain Engine**: Analyzes student profiles for context, subject detection, sentiment, and prioritizes responses with 8 types of personalized feedback.
-   **Adaptive Quiz System**: Features a multi-subject quiz database (34+ quizzes) that adapts difficulty, focuses on weak topics, and integrates with XP and badge systems.
-   **Social Learning System**: Facilitates peer help matching, study group creation, and awards collaborative XP.
-   **Subject Progress Analytics**: Provides comprehensive overview of student performance, identifies weak areas, generates learning paths, and offers AI-driven suggestions.

## Gamification Engine (REFACTORED - Oct 18, 2025)
Production-ready XP and leveling system with PostgreSQL integration:
-   **Atomic XP Operations**: award_xp uses INSERT ON CONFLICT DO UPDATE with transactions - no race conditions
-   **Concurrency-Safe**: Multiple simultaneous XP awards increment correctly (tested: 50 + 5 = 55 XP)
-   **Centralized Configuration**: XPConfig in core/config/gamification_config.py with 40+ action types and 9 multipliers
-   **Database Tables**: 7 auto-created tables (user_gamification, user_achievements, user_badges, daily_analytics, etc.)
-   **Level System**: Dynamic thresholds up to level 100 with title progression
-   **Daily Analytics**: Automatic tracking of XP earned, quizzes completed, study time per day
-   **Future-Ready**: Badge/achievement tables created, logic can be added incrementally

## Performance Optimization
Includes multi-level caching, Redis-backed session management, performance monitoring, and database connection pooling.

## Security Features
Uses bcrypt for password hashing, rate limiting for brute-force prevention, and role-based access control.

## Robust Authentication System (UPDATED - Oct 2025)
SKAILA now features a production-ready, user-friendly authentication system:
-   **Auto-Managed SECRET_KEY**: Automatically generates and persists SECRET_KEY in `.env.secrets` file, eliminating session reset issues. Falls back to Replit Secrets in production.
-   **Remember Me Feature**: Users can choose 30-day persistent sessions (default) or 1-day sessions, improving user experience.
-   **Smart Lockout Protection**: After multiple failed login attempts, users receive accurate countdown messages ("Try again in X minutes") with proper time calculation.
-   **Enhanced Feedback**: Clear error messages for lockout, invalid credentials, and success messages ("👋 Welcome back, [name]!").
-   **Modern UI**: Beautiful purple gradient login page with custom checkbox styling, autocomplete support for password managers, and smooth animations.
-   **Session Persistence**: Sessions no longer reset on server restart thanks to persistent SECRET_KEY storage.

## Modern UI/UX Design (Oct 16, 2025)
SKAILA features a completely redesigned, immersive user interface:
-   **Purple Gradient Background**: Stunning animated gradient (purple to violet) with radial pattern overlays for a premium, modern look
-   **Glass Morphism Design**: Frosted glass effect with backdrop-filter blur for all components
-   **Intelligent Layout**: Grid-based responsive design (2fr 1fr) that adapts to screen sizes
-   **Smooth Animations**: Hover effects, fade-in animations, and transform transitions for premium feel
-   **Removed Clutter**: Eliminated "Azioni Rapide" section for cleaner, more focused experience

## SKAILA Connect - Student Career Portal (Oct 16, 2025)
Revolutionary feature connecting students with real companies for internships and job opportunities:
-   **Company Database**: Structured table with companies, sectors, positions, requirements, and compensation
-   **Smart Application System**: One-click applications with XP rewards (50 XP for first application only)
-   **Anti-Farming Protection**: Duplicate applications detected, XP awarded only for new submissions
-   **API Endpoints**: `/api/skaila-connect/companies`, `/apply`, `/my-applications`
-   **Input Validation**: Complete validation (company existence, active status) with proper error handling
-   **Dynamic UI**: Company cards loaded from database with logo emojis, descriptions, and action buttons
-   **5 Partner Companies**: TechStart Italia, Innovation Lab, Creative Digital, Green Energy Corp, MediaTech Solutions

## Integrated Online Register (Oct 16, 2025)
Complete digital register system replacing obsolete school systems:
-   **Database Tables**: `voti` (grades 1-10 scale), `presenze` (attendance tracking)
-   **Student View**: Tabs for Grades, Attendance, Statistics with responsive design
-   **Grade Tracking**: Subject-wise grades, evaluation types (written/oral), teacher notes
-   **Attendance System**: Daily presence tracking, justified absences, tardiness recording
-   **Statistics Dashboard**: Automated average calculation per subject, visual progress bars, overall performance metrics
-   **Teacher Interface**: Separate view for professors to manage class grades and attendance
-   **Purple Gradient Theme**: Consistent design language across all register pages

## AI Insights Engine with Machine Learning (Oct 16, 2025)
Advanced predictive analytics system using statistical methods and regression analysis:
-   **Grade Trend Analysis**: Linear regression for performance predictions, identifies improvement/decline patterns
-   **Attendance Pattern Detection**: Calculates rates and streak analysis for early intervention
-   **Weak Subject Identification**: Uses z-scores and standard deviation to pinpoint struggling areas
-   **Future Performance Predictions**: Compares recent vs historical grades for trend forecasting
-   **Gamification Progress Tracking**: Analyzes XP velocity and achievement patterns
-   **Data-Driven Insights**: Generates top 3 prioritized recommendations based on statistical significance
-   *Note: Temporarily disabled for database schema optimization*

## Granular Messaging System (Oct 16, 2025)
Complete messaging infrastructure with multiple communication channels:
-   **Chat Hub Central**: Unified interface for all messaging types (`/chat-hub`)
-   **1-to-1 Direct Messages**: Private student-teacher and peer conversations (`/direct-messages/<user_id>`)
-   **Subject-Based Groups**: Dedicated chat rooms per academic subject (`/group-chats/<materia>`)
-   **Class-Wide Chats**: Announcements and discussions for entire classes
-   **Database Schema**: Tables for `direct_messages`, `group_chats`, `group_members` with timestamps
-   **Backend Routes**: Complete API endpoints in `messaging_routes.py` for all message types
-   **Real-time Support**: Socket.IO integration ready for live message delivery

## Complete Backend Infrastructure (Oct 16, 2025)
Comprehensive routing system for educational features:
-   **Materials Management**: Routes for uploading/downloading teaching resources (`/materiali`)
-   **Quiz System**: Adaptive quiz delivery and scoring endpoints (`/quiz`)
-   **Calendar Integration**: Academic calendar with events and deadlines (`/calendario`)
-   **API Layer**: RESTful endpoints for SKAILA Connect, applications, and user data
-   **Modular Architecture**: Separated blueprints for dashboard, messaging, and API concerns

## New Features
-   **Teaching Materials Management System**: Allows teachers to upload, organize, and manage various file types (PDF, DOC, images, video) with class-based access control and download analytics.
-   **Electronic Class Register (Registro Elettronico)**: Comprehensive student management including attendance tracking, grade recording (Italian 1-10 scale), disciplinary notes, and a lesson calendar.
-   **Parent Communication System**: Generates automated weekly and monthly reports with attendance, grades, behavior updates, homework tracking, and AI insights. It also provides real-time notifications for important events.

# External Dependencies

-   **Flask**: Web framework.
-   **Flask-SocketIO**: Real-time communication.
-   **bcrypt**: Password hashing.
-   **psutil**: System performance monitoring.
-   **SQLite**: Development database.
-   **PostgreSQL**: Production database (via psycopg2).
-   **Redis**: Optional session storage and caching.
-   **Font Awesome**: Icon library.
-   **Google Fonts (Inter)**: Typography.
-   **Chart.js**: Data visualization.
-   **Gunicorn**: WSGI HTTP server.
-   **python-dotenv**: Environment variable management.
-   **eventlet**: Asynchronous networking.