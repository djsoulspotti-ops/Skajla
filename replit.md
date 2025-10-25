# Overview

SKAILA is an educational platform for schools, connecting students, teachers, parents, and administrators in real-time. It offers a multi-role messaging system, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Designed as a Flask web application with Socket.IO for real-time communication, SKAILA is scalable and tailored for the Italian education system, aiming to enhance learning engagement and provide robust tools for school management with a focus on business vision and market potential.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask with a modular architecture, separating concerns into blueprints for authentication, dashboards, and APIs.

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
Uses bcrypt for password hashing, rate limiting, and role-based access control.

## Robust Authentication System
Features a production-ready system with auto-managed `SECRET_KEY`, "Remember Me" functionality (30-day or 1-day sessions), smart lockout protection with countdown messages, enhanced feedback, and a professional UI.

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

## Granular Messaging System
A complete messaging infrastructure with a central chat hub, supporting 1-to-1 direct messages, subject-based group chats, and class-wide chats, with dedicated database schemas and API endpoints ready for real-time Socket.IO integration.

## Complete Backend Infrastructure
Comprehensive routing system with modular architecture for educational features, including materials management, quiz system, calendar integration, and API layers for SKAILA Connect and user data.

## New Features
-   **Teaching Materials Management System**: Allows teachers to upload, organize, and manage files with class-based access control.
-   **Electronic Class Register (Registro Elettronico)**: Comprehensive student management including attendance, grades (Italian 1-10 scale), disciplinary notes, and lesson calendar.
-   **Parent Communication System**: Generates automated weekly/monthly reports with attendance, grades, behavior updates, homework, and AI insights, plus real-time notifications.

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