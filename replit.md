# Overview
SKAILA is an educational platform for the Italian education system, designed to connect students, teachers, parents, and administrators in real-time. It offers multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Built as a scalable Flask web application with Socket.IO, SKAILA aims to enhance learning engagement and provide robust tools for school management with a focus on business vision for market potential and project ambitions.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture
SKAILA is built on Flask with a modular MVC and ORM architecture using SQLAlchemy. It features a centralized configuration and a feature flag system for enabling/disabling modules. Authentication and authorization are handled by a centralized middleware supporting multi-role access. The database layer supports SQLite (development) and PostgreSQL (production) with a `DatabaseManager` for multi-tenant school management.

Real-time communication is powered by Socket.IO, enabling messaging and presence systems. AI integration focuses on personalized learning through the SKAILA AI Brain Engine, Adaptive Quiz System, and AI Insights Engine. A gamification engine provides XP and leveling with atomic and concurrency-safe operations. A study timer system tracks student sessions with XP multipliers.

The platform includes a centralized error handling framework with typed exceptions, decorators, and structured logging. The UI/UX features an enterprise design system with modern Bento Grid layouts, collapsible navigation, and role-specific dashboards for students, teachers, and principals, optimized for performance and responsive design.

A Smart Calendar & Agenda System offers personal and school-wide scheduling with role-specific behaviors, using PostgreSQL JSONB and FullCalendar.js. A Hybrid Behavioral Telemetry & Early Warning System combines client-side behavioral tracking with server-side critical event capture for struggle detection, feeding into a Teacher Early Warning Dashboard.

SKAILA also implements a Gen-Z Mobile-First UX with Progressive Web App (PWA) features, including a TikTok-style vertical feed, offline support, and push notifications. The SKAILA Connect module is an "Opportunity Marketplace" for PCTO placements, featuring dynamic student portfolios, smart matching, and a digital PCTO workflow engine for compliance and paperless operations. A Parent Dashboard provides zero-friction child monitoring with auto-generated student codes and real-time academic and attendance stats.

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
-   **openai**: AI integration
-   **Font Awesome**: Icon library
-   **Google Fonts (Inter)**: Typography
-   **Chart.js**: Data visualization
-   **Gunicorn**: WSGI HTTP server
-   **python-dotenv**: Environment variable management
-   **eventlet**: Asynchronous networking