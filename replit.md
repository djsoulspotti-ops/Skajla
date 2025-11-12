# Overview

SKAILA is an educational platform designed for the Italian education system, connecting students, teachers, parents, and administrators in real-time. It offers multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Built as a scalable Flask web application with Socket.IO, SKAILA aims to enhance learning engagement and provide robust tools for school management.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework & Patterns
SKAILA uses Flask with a modular MVC and ORM architecture, utilizing SQLAlchemy for a type-safe database layer. A centralized configuration adheres to Single Source of Truth principles.

## Feature Flags System
A production-grade modular feature control system allows schools to enable or disable specific modules such as Gamification, AI Coach, Registro Elettronico, SKAILA Connect, Materiali Didattici, Calendario, and Analytics. This system enforces feature access at both the UI and server levels, providing different responses for API and web routes, and is manageable via an admin panel.

## Authentication & Authorization
A centralized middleware handles authentication and authorization, including web and API authentication, multi-role authorization, and role-specific shortcuts.

## Database Layer
Supports both SQLite (development) and PostgreSQL (production) with a custom `DatabaseManager` for connection pooling. The schema supports multi-tenant school management, users, chat, gamification, and AI interaction tracking. Database performance is optimized with various indexes.

## Multi-Tenant School System
A comprehensive system for managing schools, classes, and teachers, including dynamic class creation, role-based registration, and automated chat room creation. It ensures isolated data for each school. Global CSRF protection, hardened session security, and multi-tenant isolation middleware prevent cross-school data access and enhance overall security.

## Real-time Communication
Socket.IO enables real-time messaging with automatic reconnection and room-based chat for various contexts (class-based, thematic, administrative). An advanced presence system with a cyberpunk aesthetic visually indicates online users.

## AI Integration
SKAILA integrates a native AI system for personalized learning through:
-   **SKAILA AI Brain Engine**: Analyzes student profiles for context.
-   **Adaptive Quiz System**: Adjusts difficulty and focuses on weak topics.
-   **Social Learning System**: Facilitates peer help and collaborative XP.
-   **Subject Progress Analytics**: Provides performance overview and AI-driven learning path suggestions.
-   **AI Insights Engine**: Uses statistical methods for grade trends, attendance, and performance predictions.

## Gamification Engine
A production-ready XP and leveling system with PostgreSQL integration, featuring atomic and concurrency-safe XP operations, centralized configuration for over 40 action types and multipliers, dynamic level progression, and daily analytics tracking.

## Study Timer System
A production-ready time management system for tracking student study sessions with precise pause/resume functionality. It includes four session types (Focus, Pomodoro, Deep Work, Review) with XP multipliers and a REST API.

## Security Features
Includes bcrypt password hashing, per-user session expiry, SQL injection prevention, comprehensive HTTP security headers, CSRF protection, and Flask-Limiter for rate limiting.

## Enterprise UI Design System
Features an ultra-professional, enterprise-grade UI with a new design token and color system, modern fonts (Inter, IBM Plex Sans, JetBrains Mono), and a 4px spacing system. It is mobile-first, WCAG AA accessible, and performance-optimized.

## Key Features
-   **SKAILA Connect**: A student career portal with a company database.
-   **Integrated Online Register**: Digital register for grades and attendance.
-   **Teaching Materials Management System**: Allows teachers to manage files with class-based access control.
-   **Parent Communication System**: Generates automated reports with AI insights and real-time notifications.

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