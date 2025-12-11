# Overview
SKAJLA is an educational platform for the Italian education system, connecting students, teachers, parents, and administrators in real-time. It provides multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Built as a scalable Flask web application with Socket.IO, SKAJLA aims to enhance learning engagement and provide robust tools for school management with a focus on business vision for market potential and project ambitions.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture
SKAJLA is built on Flask with a modular MVC and ORM architecture using SQLAlchemy, supporting SQLite (development) and PostgreSQL (production). It features centralized configuration, a feature flag system, and multi-role authentication/authorization. Real-time communication is powered by Socket.IO for messaging and presence.

Key features include:
-   **AI Integration**: Personalized learning via the SKAJLA AI Brain Engine, Adaptive Quiz System (164 quizzes across 9 subjects, aligned with Italian curriculum, adaptive difficulty), and AI Insights Engine. The AI Coach is powered by Google Gemini 2.0-flash and integrated directly into the student dashboard, offering personalized, motivational tutoring in Italian and XP rewards for interactions.
-   **Advanced Gamification V2 System**: Includes a 9-level Rank System (Germoglio → Immortale), Battle Pass, daily/weekly/class Challenge System, Kudos for peer recognition, Power-ups (boosters), multi-period Leaderboards, and rarity-tiered Badges. A student-facing `/gamification` dashboard uses a Bento Grid layout for a modern, responsive display of progression, challenges, badges, leaderboards, and more. Chatbot interactions are integrated with the gamification system for streak updates, challenge progress, and XP rewards.
-   **UI/UX**: Features an enterprise design system with modern Bento Grid layouts, collapsible navigation, role-specific dashboards (Student, Teacher, Principal), and a Gen-Z Mobile-First UX with PWA features (TikTok-style feed, offline support, push notifications). The messaging system has a futuristic cyberpunk aesthetic with glassmorphism, neon glow effects, and a 3D orbital online indicator. Student dashboards feature Teams-style single-page navigation with panels for Dashboard, AI Coach, Calendario, and Gamification, including real-time grades, attendance, and Chart.js grade trends. The Principal Dashboard offers executive-level analytics including school overview, class analytics, anonymous teacher ratings, economic KPIs, and platform engagement metrics, all with full tenant isolation.
-   **Core Systems**:
    -   **Unified Messaging System**: Real-time messaging with enhanced features like heartbeat/ping-pong, read receipts, delivery confirmations, role-based notifications, broadcast announcements, and class/subject rooms with robust security and rate limiting.
    -   **Study Groups (Gruppi di Studio)**: Collaborative study groups for students with real-time Socket.IO chat, shared task management, file sharing, and member management. Features include group creation, invite system (max 8-10 members), tabs for Chat/Tasks/Members, and full authorization controls with membership verification on all endpoints.
    -   **Smart Calendar & Agenda System**: Personal and school-wide scheduling with role-specific behaviors.
    -   **Hybrid Behavioral Telemetry & Early Warning System**: Client-side behavioral tracking combined with server-side critical event capture, feeding into a Teacher Early Warning Dashboard.
    -   **SKAJLA Connect**: An "Opportunity Marketplace" for PCTO placements with dynamic student portfolios, smart matching, and a digital workflow engine.
    -   **Parent Dashboard**: Zero-friction child monitoring with auto-generated student codes and real-time academic and attendance stats.
    -   **Error Handling**: Centralized framework with typed exceptions and structured logging.
    -   **Autoscale Deployment Fixes**: Health check endpoints, fast path for root endpoint, safe database migration methods, Redis configuration for caching, and Gunicorn optimization for cloud deployment.

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
-   **google-genai**: Google Gemini 2.0-flash API for AI tutoring
-   **Font Awesome**: Icon library
-   **Google Fonts (Inter)**: Typography
-   **Chart.js**: Data visualization
-   **Gunicorn**: WSGI HTTP server
-   **python-dotenv**: Environment variable management
-   **eventlet**: Asynchronous networking