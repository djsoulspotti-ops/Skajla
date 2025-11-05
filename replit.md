# Overview

SKAILA is an educational platform connecting students, teachers, parents, and administrators in real-time. It offers multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Designed as a Flask web application with Socket.IO, SKAILA is scalable, tailored for the Italian education system, and aims to enhance learning engagement and provide robust tools for school management.

# Recent Changes (November 05, 2025)

## Circulating Avatars - Real-Time Presence Indicator 🎯
1. **Visual Presence System** - Online users' avatars now orbit smoothly around the messaging button, providing instant visual feedback of who's currently online in the school
2. **Smooth 60fps Animation**:
   - CSS GPU-accelerated orbital motion (15s full rotation)
   - Avatars display user initials with color-coded backgrounds
   - Hover to pause animation and see user tooltips with full names
   - Responsive design (smaller avatars/orbit on mobile)
3. **Real-Time Updates via Socket.IO**:
   - Listens to `user_connected` and `user_disconnected` events
   - Automatically refreshes online users list when presence changes
   - Fallback periodic refresh every 30 seconds
4. **Technical Implementation**:
   - **API Endpoint**: `/api/online-users` returns up to 7 online users from same school
   - **JavaScript Component**: `CirculatingAvatars` class in `static/js/circulating-avatars.js`
   - **CSS Animations**: Keyframe-based orbit in `static/css/circulating-avatars.css`
   - **Integration**: Dashboard sidebar messaging button wrapped in circulating avatar container
5. **Features**: Color-coded avatars, smooth fade-in/out transitions, tooltip on hover, pause on hover, mobile-responsive

## Feature Flags System - PRODUCTION READY ✅ (November 01, 2025)
1. **Modular Feature Control** - Schools can now enable/disable specific modules (Gamification, AI Coach, Registro Elettronico, SKAILA Connect, Materiali Didattici, Calendario, Analytics) via admin panel at `/admin/features`.
2. **Dual-Layer Security**:
   - **UI Layer**: Disabled features show as greyed-out buttons with 🔒 icon, "Premium" badge, and tooltip messaging
   - **Server Layer**: `before_request` hooks on all blueprints (registro_bp, credits_bp, ai_chat_bp, skaila_connect_bp) enforce feature flags with:
     - API routes (`/api/...`): Return JSON 403 with `upgrade_required: true` flag
     - Web routes: Redirect to dashboard with flash warning message
3. **Path-Based Detection** - Uses `request.path.startswith('/api/')` for reliable API vs web differentiation (works for GET, POST, PUT, DELETE)
4. **School Features Manager** - Centralized `school_features_manager` with `school_features` table for per-school, per-feature granular control
5. **Admin Presets** - Quick "Gamification Only" preset available for schools wanting minimal feature set

## Previous Bug Fixes (October 30, 2025)
1. **Security Fix: Multi-Tenant Isolation** - Fixed critical cross-school data leak in dashboard professore. Query `docenti_classi` now JOINs with `classi` table and filters by `scuola_id` to ensure tenant isolation.
2. **Dashboard Professore Fix** - `classi_attive` now calculated dynamically from `docenti_classi` table instead of hardcoded placeholder value.
3. **Role Consistency Fix** - Teaching materials manager now consistently supports `professore/docente/dirigente` roles across upload, list, and search operations.
4. **Database Compatibility** - Database manager correctly converts PostgreSQL placeholders (`%s`) to SQLite placeholders (`?`) for cross-database compatibility.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework & Patterns
The application uses Flask with a modular architecture, adhering to MVC and ORM patterns. SQLAlchemy provides a type-safe database layer. A centralized configuration system implements Single Source of Truth principles for consistency across core settings, security, caching, feature flags, and gamification parameters.

## Feature Flags System (NEW - Production Ready)
A production-grade modular feature control system allowing schools to enable/disable specific modules:
-   **Available Features**: `gamification`, `ai_coach`, `registro_elettronico`, `skaila_connect`, `materiali_didattici`, `calendario`, `analytics`
-   **SchoolFeaturesManager** (`services/school/school_features_manager.py`): Centralized manager with `school_features` table (school_id, feature_name, enabled)
-   **Feature Guard Middleware** (`shared/middleware/feature_guard.py`): 
    - `check_feature_enabled(school_id, feature_name)` helper function
    - `Features` class with constants to avoid typos
-   **Blueprint Protection**: `before_request` hooks on all critical blueprints:
    - `routes/registro_routes.py`: Protects all 12 registro API endpoints
    - `routes/credits_routes.py`: Protects gamification views and API
    - `routes/ai_chat_routes.py`: Protects AI Coach chat and suggestions
    - `routes/skaila_connect_routes.py`: Protects career portal
-   **Dual Response System**:
    - API routes (`/api/*`): Return JSON 403 with structured error + `upgrade_required: true`
    - Web routes: Redirect to dashboard with flash warning message
-   **UI Integration**: Dashboard templates conditionally render disabled state with CSS classes, lock icons, premium badges, and tooltips
-   **Admin Panel**: Directors can manage features at `/admin/features` with quick presets

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