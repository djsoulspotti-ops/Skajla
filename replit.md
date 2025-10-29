# Overview

SKAILA is an educational platform for schools, connecting students, teachers, parents, and administrators in real-time. It offers a multi-role messaging system, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Designed as a Flask web application with Socket.IO for real-time communication, SKAILA is scalable and tailored for the Italian education system, aiming to enhance learning engagement and provide robust tools for school management with a focus on business vision and market potential.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask with a modular architecture, separating concerns into blueprints for authentication, dashboards, and APIs.

## Shared Middleware (October 2025 - Refactoring)
**Centralized Authentication & Authorization**: All authentication decorators consolidated in `shared/middleware/auth.py` eliminating 5+ code duplications. Provides:
- `require_login`: Web route authentication with redirect
- `require_auth` / `api_auth_required`: API authentication with JSON response
- `require_role(*roles)`: Multi-role authorization
- `require_admin`, `require_teacher`, `require_student`: Role-specific shortcuts
- Utility functions: `get_current_user()`, `is_authenticated()`, `has_role()`, `has_any_role()`

## Centralized Configuration System (SSoT)
SKAILA implements Single Source of Truth principles with centralized, modular configuration for core settings, security, caching, feature flags, gamification parameters (XP actions, multipliers, levels, badges, streaks), and shared validators/formatters. This approach reduces code, ensures consistency, and improves maintainability.

## Database Layer
Supports both SQLite (development) and PostgreSQL (production) with a custom `DatabaseManager` for connection pooling. The schema supports multi-tenant school management, users, chat, gamification, and AI interaction tracking.

## Multi-Tenant School System
Includes a comprehensive school, class, and teacher management system with dynamic class creation, role-based registration, and automated chat room creation, supporting isolated data for unlimited schools.

## Real-time Communication
Socket.IO provides real-time messaging with automatic reconnection and room-based chat for various types (class-based, thematic, administrative).

## AI Integration
A native SKAILA AI system powers personalized learning through:
-   **SKAILA AI Brain Engine**: Analyzes student profiles for context, subject, sentiment, and provides personalized feedback.
-   **Adaptive Quiz System**: Multi-subject quizzes adapt difficulty and focus on weak topics, integrating with gamification.
-   **Social Learning System**: Facilitates peer help and study groups, awarding collaborative XP.
-   **Subject Progress Analytics**: Provides performance overview, identifies weak areas, and offers AI-driven learning path suggestions.
-   **AI Insights Engine**: Uses statistical methods and regression analysis for grade trend analysis, attendance pattern detection, weak subject identification, and future performance predictions.

## Gamification Engine
A production-ready XP and leveling system with PostgreSQL integration, featuring atomic and concurrency-safe XP operations, centralized configuration for over 40 action types and multipliers, dynamic level progression up to 100, and daily analytics tracking.

## Performance Optimization
Includes multi-level caching, Redis-backed session management, performance monitoring, and database connection pooling.

## Security Features
**Production-Grade Security Implementation (October 2025):**
-   **Password Security**: bcrypt hashing with robust password validation policy (8+ characters, uppercase, number, lowercase required) via `services/password_validator.py`
-   **Session Management**: Per-user session expiry tracking with automatic timeout handling and flash notifications
-   **SQL Injection Prevention**: All queries use PostgreSQL parameterized placeholders (%s), zero raw string interpolation
-   **Security Headers**: Comprehensive HTTP headers (HSTS, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, CSP) implemented in main.py
-   **Demo Mode Isolation**: Secure demo system via `routes/demo_routes.py` using only mock data, zero database access for demo users (-999/-998)
-   **CSRF Protection**: Already present and functional across forms and API endpoints
-   **Rate Limiting**: Flask-Limiter integration for critical routes

## Robust Authentication System
Features a production-ready system with auto-managed `SECRET_KEY`, "Remember Me" functionality (30-day or 1-day sessions), smart lockout protection with countdown messages, enhanced feedback, and a professional UI. Includes intelligent registration flow with auto-class detection and instant chat room access.

## Enterprise UI Design System
SKAILA features an ultra-professional, enterprise-grade UI redesigned for corporate teams. Key elements include:
-   **Design Tokens & Color System**: New enterprise palette with deep corporate blues, steel greys, classic gold accents, and semantic colors. Utilizes Inter, IBM Plex Sans, and JetBrains Mono fonts, a 4px spacing system, and sophisticated shadow elevation.
-   **Redesigned Templates**: All pages (Homepage, Login, Registration, Student/Teacher Dashboards, Calendar) have been rebuilt with professional layouts, clean forms, and intuitive navigation. The calendar features dynamic JavaScript for full month/year navigation and interactive day cells.
-   **Professional Components**: Standardized cards, buttons, forms, tables, and KPI cards with clean aesthetics and proper states.
-   **Removed Gaming Elements**: Eliminates neon glows, animated grids, and vibrant color schemes for a clean, flat design with subtle depth.
-   **Technical Implementation**: Centralized `tokens.css` (350+ lines), modular CSS, mobile-first responsive design, WCAG AA accessibility, and optimized performance.

## SKAILA Connect - Student Career Portal
A feature connecting students with companies for internships and job opportunities, including a company database, smart one-click application system with XP rewards, anti-farming protection, and dynamic UI for company listings.

## Integrated Online Register
A complete digital register system with database tables for grades (`voti`) and attendance (`presenze`). It provides student views for grades, attendance, and statistics, a teacher interface for management, and automated average calculations and progress bars.

## Granular Messaging System with Auto-Enrollment
A complete messaging infrastructure with a central chat hub, supporting 1-to-1 direct messages, subject-based group chats, and class-wide chats. **NEW (October 2025):** Intelligent auto-creation and enrollment into class chat rooms during student registration - new students are automatically added to their class chat room for immediate peer communication.

## Complete Backend Infrastructure
Comprehensive routing system with modular architecture for educational features, including materials management, quiz system, calendar integration, and API layers for SKAILA Connect and user data.

## New Features
-   **Teaching Materials Management System**: Allows teachers to upload, organize, and manage files with class-based access control.
-   **Electronic Class Register (Registro Elettronico)**: Comprehensive student management including attendance, grades (Italian 1-10 scale), disciplinary notes, and lesson calendar.
-   **Parent Communication System**: Generates automated weekly/monthly reports with attendance, grades, behavior updates, homework, and AI insights, plus real-time notifications.

# Project Structure (October 2025 - Reorganized)

```
/
├── main.py                    # Application entry point
├── wsgi.py                    # WSGI configuration
├── gunicorn.conf.py          # Gunicorn production config
├── requirements.txt          # Python dependencies (updated)
├── replit.md                 # This file
│
├── services/                 # Business logic organized by domain
│   ├── ai/                   # AI & Chatbot services
│   │   ├── ai_chatbot.py
│   │   ├── coaching_engine.py
│   │   ├── skaila_ai_brain.py
│   │   └── ai_insights_engine.py
│   ├── gamification/         # XP, levels, badges system
│   │   ├── gamification.py
│   │   └── skaila_quiz_manager.py
│   ├── school/              # School management
│   │   ├── school_system.py
│   │   ├── registro_elettronico.py
│   │   └── teaching_materials_manager.py
│   ├── database/            # Database layer
│   │   ├── database_manager.py
│   │   └── database_keep_alive.py
│   ├── monitoring/          # Performance & caching
│   │   ├── performance_cache.py
│   │   └── production_monitor.py
│   ├── reports/             # Report generation
│   │   ├── report_scheduler.py
│   │   └── report_generator.py
│   ├── security/            # Security modules
│   │   └── csrf_protection.py
│   └── utils/               # Shared utilities
│       ├── environment_manager.py
│       ├── session_manager.py
│       └── email_sender.py
│
├── routes/                  # HTTP endpoints (blueprints)
│   ├── auth_routes.py
│   ├── dashboard_routes.py
│   ├── messaging_routes.py
│   ├── api_routes.py
│   └── demo_routes.py (secure isolated demo)
│
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JS, images
│   └── css/
│       └── tokens.css       # Enterprise design system
│
├── scripts/                 # Maintenance & utility scripts
├── docs/                    # Project documentation (NEW)
│   ├── API_REGISTRO_ELETTRONICO.md
│   ├── BACKEND_COMPLETATO.md
│   └── GUIDA_SVILUPPATORI.md
│
└── examples/                # Code examples & integration templates
```

**Note:** Bridge files exist in root for backward compatibility during migration. All actual code is in organized `/services` folders.

# External Dependencies

-   **Flask**: Web framework
-   **Flask-SocketIO**: Real-time communication
-   **Flask-Compress**: Response compression
-   **Flask-Limiter**: Rate limiting
-   **bcrypt**: Password hashing
-   **PyJWT**: JWT token handling
-   **authlib**: OAuth integration
-   **psutil**: System performance monitoring
-   **PostgreSQL**: Production database (via psycopg2)
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