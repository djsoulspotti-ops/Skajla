# Overview
SKAILA is an educational platform for the Italian education system, designed to connect students, teachers, parents, and administrators in real-time. It offers multi-role messaging, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. Built as a scalable Flask web application with Socket.IO, SKAILA aims to enhance learning engagement and provide robust tools for school management with a focus on business vision for market potential and project ambitions.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture
SKAILA is built on Flask with a modular MVC and ORM architecture using SQLAlchemy. It features a centralized configuration and a feature flag system for enabling/disabling modules. Authentication and authorization are handled by a centralized middleware supporting multi-role access. The database layer supports SQLite (development) and PostgreSQL (production) with a `DatabaseManager` for multi-tenant school management.

Real-time communication is powered by Socket.IO, enabling messaging and presence systems. AI integration focuses on personalized learning through the SKAILA AI Brain Engine, Adaptive Quiz System, and AI Insights Engine.

## Advanced Gamification V2 System
The platform features an extensive gamification system with:
- **Rank System**: 9 progression levels from Germoglio → Immortale with XP thresholds (200 to 13000+ XP)
- **Battle Pass**: Seasonal content with free and premium reward tracks
- **Challenge System**: Daily, weekly, and class challenges with auto-assignment
- **Kudos**: Peer recognition system awarding XP for appreciation
- **Power-ups**: Purchasable boosters (XP multipliers, streak shields, second chances)
- **Leaderboards**: Multi-period rankings (daily/weekly/monthly/seasonal/lifetime)
- **Badges**: Achievement unlocks with rarity tiers (comune/raro/epico/leggendario)
- **Notifications**: Real-time gamification alerts for rank ups, badges, and challenges

### Student Gamification Dashboard (November 2025)
Full-featured student-facing UI at `/gamification`:
- **Bento Grid Layout**: Modern responsive design with profile card, streak tracker, challenges, badges, leaderboard
- **Profile Card**: Rank icon with gradient color, XP progress bar, next rank preview
- **Challenges Section**: Daily/weekly challenge cards with countdown timers and progress bars
- **Badges Showcase**: Grid of earned badges with rarity indicators and modal for full collection
- **Leaderboard Widget**: Multi-period tabs (weekly/monthly/lifetime) with live rankings
- **Power-ups Section**: Available boosters with activation buttons
- **Kudos Feed**: Recent peer recognition with XP awards
- **Activity Timeline**: Recent gamification events (XP gains, badges, challenge completions)
- **Ranks Progression**: Visual ladder showing all 9 ranks with current position highlighted

API: `/api/gamification/v2/*` - Complete REST endpoints for profile, stats, challenges, badges, leaderboards, kudos, power-ups, and activity timeline.

A study timer system tracks student sessions with XP multipliers.

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