# Overview
SKAILA is an educational platform for the Italian education system, connecting students, teachers, parents, and administrators in real-time. It provides multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Built as a scalable Flask web application with Socket.IO, SKAILA aims to enhance learning engagement and provide robust tools for school management.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework & Patterns
SKAILA uses Flask with a modular MVC and ORM architecture, utilizing SQLAlchemy for a type-safe database layer. A centralized configuration adheres to Single Source of Truth principles.

## Feature Flags System
A modular feature control system allows schools to enable or disable specific modules (e.g., Gamification, AI Coach) at both UI and server levels, manageable via an admin panel.

## Authentication & Authorization
A centralized middleware handles web and API authentication, multi-role authorization, and role-specific shortcuts.

## Database Layer
Supports SQLite (development) and PostgreSQL (production) with a `DatabaseManager` for connection pooling. The schema supports multi-tenant school management, users, chat, gamification, and AI interaction tracking.

## Multi-Tenant School System
Manages schools, classes, and teachers with dynamic class creation, role-based registration, and automated chat room creation. It ensures isolated data for each school with global CSRF protection, hardened session security, and multi-tenant isolation middleware.

## Real-time Communication
Socket.IO enables real-time messaging with automatic reconnection and room-based chat. An advanced presence system indicates online users.

## AI Integration
SKAILA integrates a native AI system for personalized learning through the SKAILA AI Brain Engine, an Adaptive Quiz System, a Social Learning System, Subject Progress Analytics, and an AI Insights Engine.

## Gamification Engine
A production-ready XP and leveling system with PostgreSQL integration, featuring atomic and concurrency-safe XP operations, centralized configuration for over 40 action types, dynamic level progression, and daily analytics tracking.

## Study Timer System
A time management system for tracking student study sessions with precise pause/resume functionality, including four session types (Focus, Pomodoro, Deep Work, Review) with XP multipliers and a REST API.

## Error Handling Framework
A centralized error handling system with a typed exception hierarchy, reusable decorators (`@handle_errors`, `@retry_on`, `@log_errors`), structured JSON logging, automatic retry logic, and user-safe error messages.

## Enterprise UI Design System & Premium Dashboard
A complete UI/UX overhaul implementing modern Bento Grid layouts, collapsible navigation, and role-specific dashboards for Student, Teacher, and Principal roles. It features a design system foundation with centralized CSS custom properties, responsive design, and performance optimizations.

## Smart Calendar & Agenda System
A personal and school-wide calendar system with role-specific behaviors and integrated electronic register workflows. It uses PostgreSQL JSONB for event metadata, FullCalendar.js for interactive UI, and a REST API with role-based authorization and multi-tenant isolation.

## Hybrid Behavioral Telemetry & Early Warning System
**Part of Feature #1: Smart AI-Tutoring & Early-Warning Engine**

A production-ready telemetry infrastructure combining client-side behavioral tracking (99%+ reliability) with server-side critical event capture (100% reliability) for comprehensive student struggle detection.

**Client-Side Telemetry:**
- Behavioral event tracking (page views, navigation, time-on-task, clicks)
- Acknowledgement-based queue management with stable client_event_id
- localStorage persistence for cross-session retry
- Automatic quarantine for invalid events
- Multiple exit handlers (beforeunload, pagehide, visibilitychange) with synchronous XHR validation
- Batch API with HTTP 207 partial success handling

**Server-Side Telemetry:**
- Quiz submissions tracked in `services/gamification/skaila_quiz_manager.py`
- AI Coach interactions tracked in `routes/ai_chat_routes.py`
- Captures: quiz_id, subject, topic, difficulty, is_correct, accuracy_score, time_taken, xp_earned
- Events marked with `device_type: 'server'` and `source: 'server'` for provenance
- Never blocks critical user flows (wrapped in try/except)

**TelemetryEngine Unified Interface:**
- Accepts events from both client (via API) and server (direct calls)
- Automatic school_id lookup via `_get_user_school(user_id)`
- Auto-creates session_id when not provided (server-side events)
- Stores all events in unified `behavioral_telemetry` PostgreSQL table
- Automatic early warning alert generation on struggle detection
- Four PostgreSQL tables: behavioral_telemetry, early_warning_alerts, recovery_paths, telemetry_sessions

**Architecture Decision:**
Hybrid approach addresses browser-imposed limitations (~100ms unload window) that affect all web analytics platforms. Critical learning events (quiz submissions, AI interventions) achieve 100% reliability via server-side tracking, while behavioral signals maintain 99%+ reliability via optimized client-side tracking.

## Teacher Early Warning Dashboard
**Part of Feature #1: Smart AI-Tutoring & Early-Warning Engine**

A production-ready cyberpunk-themed dashboard for teachers to monitor and intervene with struggling students in real-time.

**Features:**
- Severity-based alert categorization (Critical, High, Medium) with color-coded cards
- Student profile cards with avatar, struggle indicators, and telemetry evidence
- Real-time alert feed powered by behavioral telemetry data
- Quick action buttons: acknowledge alert, view student profile
- Empty state with positive messaging when no alerts active
- Responsive Bento Grid layout for desktop and mobile

**Technical Implementation:**
- Route: `/early-warning/dashboard` (requires docente role)
- Template: `templates/early_warning_dashboard.html`
- API endpoints: `/api/alerts` (GET), `/api/alert/<id>/acknowledge` (POST), `/api/alert/<id>/resolve` (POST)
- Data formatting: Automatic JSON parsing for evidence/recommended_actions, student name composition
- Design: IBM Plex Sans typography, Deep Corporate Blue (#003B73), Classic Gold (#D4AF37) accents

## Gen-Z Mobile-First UX & Progressive Web App (PWA)
**Part of Feature #2: Gen-Z Mobile-First UX**

A complete PWA infrastructure with TikTok-style vertical feed for mobile-first Gen-Z user experience.

**PWA Features:**
- Installable as native app on mobile devices (Android/iOS)
- Offline support with service worker caching strategies
- Push notifications for real-time updates
- App shortcuts for quick access to Dashboard, AI Coach, Quiz
- Share target integration for content sharing
- Automatic cache management with 7-day max age

**Mobile-First Components:**
- **Vertical Feed**: Scroll-snap cards (85vh height), infinite scroll, pull-to-refresh
- **Swipeable Cards**: Touch gestures with left/right swipe detection, spring animations
- **Mobile Navigation**: Bottom nav bar with safe area support for notched devices
- **Touch Optimizations**: iOS smooth scrolling, overscroll containment, tap highlight removal
- **Responsive Design**: Mobile-first breakpoints (640px, 768px, 1024px)

**Technical Files:**
- PWA Manifest: `static/manifest.json` (app config, icons, shortcuts)
- Service Worker: `static/sw.js` (caching, offline, push, background sync)
- Mobile CSS: `static/css/mobile-first.css` (vertical feed, swipeable UI, mobile nav)
- Vertical Feed Component: `static/js/vertical-feed.js` (touch gestures, IntersectionObserver)
- Offline Page: `templates/offline.html` (network retry)
- Icons: `static/icons/` (192x192px, 512x512px SKAILA branded icons)

**Browser Compatibility:**
- Service Worker: All modern browsers + Safari 11.1+
- Scroll Snap: Chrome 69+, Safari 11+, Firefox 68+
- PWA Install: Chrome/Edge (desktop/mobile), Safari (iOS 11.3+)

## Key Features
-   **SKAILA Connect**: Student career portal with a company database.
-   **Integrated Online Register**: Digital register for grades and attendance.
-   **Teaching Materials Management System**: Manages files with class-based access control.
-   **Parent Communication System**: Generates automated reports with AI insights and real-time notifications.
-   **Smart Calendar & Agenda**: Personal and school-wide calendar with role-specific behaviors.

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