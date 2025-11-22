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