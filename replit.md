# Overview

SKAILA is an educational platform connecting students, teachers, parents, and administrators in real-time. It offers multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Designed as a Flask web application with Socket.IO, SKAILA is scalable, tailored for the Italian education system, and aims to enhance learning engagement and provide robust tools for school management.

# Recent Changes (October 30, 2025)

## Critical Bug Fixes
1. **Security Fix: Multi-Tenant Isolation** - Fixed critical cross-school data leak in dashboard professore. Query `docenti_classi` now JOINs with `classi` table and filters by `scuola_id` to ensure tenant isolation.
2. **Dashboard Professore Fix** - `classi_attive` now calculated dynamically from `docenti_classi` table instead of hardcoded placeholder value.
3. **Role Consistency Fix** - Teaching materials manager now consistently supports `professore/docente/dirigente` roles across upload, list, and search operations.
4. **Database Compatibility** - Database manager correctly converts PostgreSQL placeholders (`%s`) to SQLite placeholders (`?`) for cross-database compatibility.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework & Patterns
The application uses Flask with a modular architecture, adhering to MVC and ORM patterns. SQLAlchemy provides a type-safe database layer. A centralized configuration system implements Single Source of Truth principles for consistency across core settings, security, caching, feature flags, and gamification parameters.

## Authentication & Authorization
A centralized middleware handles all authentication and authorization decorators, including web route and API authentication, multi-role authorization, and role-specific shortcuts.

## Database Layer
Supports both SQLite (development) and PostgreSQL (production) with a custom `DatabaseManager` for connection pooling. The schema supports multi-tenant school management, users, chat, gamification, and AI interaction tracking.

## Multi-Tenant School System
Includes a comprehensive school, class, and teacher management system with dynamic class creation, role-based registration, and automated chat room creation, supporting isolated data for unlimited schools.

## Real-time Communication
Socket.IO provides real-time messaging with automatic reconnection and room-based chat for various types (class-based, thematic, administrative). Intelligent auto-creation and enrollment into class chat rooms occur during student registration.

## AI Integration
A native SKAILA AI system powers personalized learning through:
-   **SKAILA AI Brain Engine**: Analyzes student profiles for context and sentiment.
-   **Adaptive Quiz System**: Quizzes adapt difficulty and focus on weak topics.
-   **Social Learning System**: Facilitates peer help and awards collaborative XP.
-   **Subject Progress Analytics**: Provides performance overview and AI-driven learning path suggestions.
-   **AI Insights Engine**: Uses statistical methods for grade trend analysis, attendance patterns, and performance predictions.

## Gamification Engine
A production-ready XP and leveling system with PostgreSQL integration, featuring atomic and concurrency-safe XP operations, centralized configuration for over 40 action types and multipliers, dynamic level progression, and daily analytics tracking. Integrated with the Study Timer for automatic XP rewards.

## Study Timer System
A production-ready time management system for student study session tracking with accurate pause/resume functionality. It includes a PostgreSQL table for session data, precise pause tracking, four session types (Focus, Pomodoro, Deep Work, Review) with XP multipliers, and a REST API with 8 endpoints. XP rewards are calculated at 2 XP per active minute plus a 50 XP bonus for sessions 25 minutes or longer.

## Security Features
Production-grade security includes bcrypt password hashing with strong validation, per-user session expiry, SQL injection prevention via parameterized queries, comprehensive HTTP security headers, CSRF protection, and Flask-Limiter for rate limiting. A secure demo mode uses mock data with no database access.

## Enterprise UI Design System
SKAILA features an ultra-professional, enterprise-grade UI with a new design token and color system (deep corporate blues, steel greys, gold accents), Inter, IBM Plex Sans, and JetBrains Mono fonts, and a 4px spacing system. All templates are redesigned for professional layouts. The UI is mobile-first, WCAG AA accessible, and optimized for performance.

## Key Features
-   **SKAILA Connect**: Student career portal with company database and smart application system.
-   **Integrated Online Register**: Digital register for grades (`voti`) and attendance (`presenze`) with student and teacher interfaces.
-   **Teaching Materials Management System**: Allows teachers to upload, organize, and manage files with class-based access control.
-   **Parent Communication System**: Generates automated weekly/monthly reports with AI insights and real-time notifications.

## Project Structure
The project utilizes a reorganized structure with `core/` for MVC and ORM architecture, `shared/` for utilities and middleware, `services/` for business logic by domain, `routes/` for HTTP endpoints, `templates/` for Jinja2 HTML templates, and `static/` for CSS, JS, and images.

# External Dependencies

-   **Flask**: Web framework
-   **Flask-SocketIO**: Real-time communication
-   **Flask-Compress**: Response compression
-   **Flask-Limiter**: Rate limiting
-   **bcrypt**: Password hashing
-   **PyJWT**: JWT token handling
-   **authlib**: OAuth integration
-   **psutil**: System performance monitoring
-   **PostgreSQL**: Production database
-   **redis**: Caching layer
-   **APScheduler**: Task scheduling
-   **replit-object-storage**: File storage
-   **openai**: AI integration (optional)
-   **Font Awesome**: Icon library
-   **Google Fonts (Inter)**: Typography
-   **Chart.js**: Data visualization
-   **Gunicorn**: WSGI HTTP server
-   **python-dotenv**: Environment variable management
-   **eventlet**: Asynchronous networking