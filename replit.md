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

# Recent Updates (December 2025)
- **Teams-Style Single-Page Navigation**: Student dashboard now uses panel-based navigation like Microsoft Teams:
  - Clicking sidebar items switches content panels WITHOUT page reload
  - Smooth CSS slide-in transitions between panels
  - Four main panels: Dashboard, AI Coach, Calendario, Gamification
  - Active state styling on sidebar items
  - Mobile bottom navigation also uses panel switching
- **Enhanced Student Dashboard**: Complete redesign with Bento Grid layout featuring:
  - Real-time grades table with color-coded badges (excellent/good/pass/fail)
  - Subject averages with icons and automatic media calculation
  - Attendance statistics with progress bars and detailed breakdown
  - Chart.js grade trends visualization (last 90 days)
  - Upcoming events/tests from calendar
  - Quick stats cards (media generale, frequenza %, XP totali, streak)
  - All data is read-only from voti and presenze tables with tenant isolation (scuola_id filtering)
- **Embedded AI Coach Panel**: AI Chat interface integrated directly into student dashboard as a panel:
  - Full chat interface with message input and send button
  - Welcome card with suggestions and gamification stats
  - XP badge showing current XP earned from chat interactions
  - Message history area with typing indicator
  - Auto-focus on input when switching to panel
- **Gemini 2.0 AI Integration**: AI Coach powered by Google Gemini 2.0-flash model for intelligent conversational tutoring
  - Demo endpoint at `/demo/ai/chat` works without authentication
  - Personalized responses based on student's gamification context (rank, XP, streak)
  - Italian language support with motivational coaching style
- **XP Reward System**: Chat interactions award 5-50 XP with automatic rank progression and gamification context refresh
- **Test Accounts Created**: Student (test123), Teacher (prof123), Admin (admin123) accounts with proper bcrypt password hashes
- **Status**: Gemini API key active, chatbot powered by Gemini 2.0-flash model
- **UX Enhancements (December 2025)**: Applied usability engineering principles to dashboards:
  - **Fitts' Law**: Minimum 44-48px click targets for all interactive elements, larger touch areas on mobile
  - **Hick's Law**: Enhanced visual hierarchy with primary action emphasis and clearer decision paths
  - **Gestalt Principles**: Improved proximity grouping, consistent spacing rhythm, similarity in interactive states
  - **Accessibility**: Focus-visible outlines, reduced-motion support, WCAG-compliant contrast
  - **PWA**: Created offline.html fallback page, updated service worker cache versioning
- **Telemetry Resilience Architecture**: Centralized user validation at API route level (telemetry_routes.py):
  - All telemetry endpoints validate user existence BEFORE database operations
  - Invalid sessions return 401 with `require_reauth: true` flag
  - Duplicate database queries eliminated from telemetry_engine.py
  - Prevents ForeignKeyViolation errors at database layer
- **Principal Dashboard (December 2025)**: Comprehensive executive dashboard at `/dashboard/dirigente`:
  - **School Overview**: Total students, teachers, classes, average student age, active users today
  - **Classes Analytics**: Student count, average grade, attendance rate per class with color-coded badges
  - **Teachers with Anonymous Ratings**: 5-star rating system from students, rating count, subject display
  - **Economic KPIs**: Monthly revenue (€599/month Professional tier), cost per student, revenue trend chart
  - **Platform Engagement**: 7-day engagement rate, AI Coach usage stats, gamification participation, parent engagement
  - **Visualizations**: Chart.js for revenue trends and grade distribution, bento grid layout
  - **Security**: Full tenant isolation - ALL queries filter by scuola_id, no cross-school data exposure
  - **Test Account**: dirigente@skaila.app / password123 (School ID: 1)
  - **Database**: teacher_ratings table for anonymous student feedback
- **Italian Curriculum-Aligned Quiz System (December 2025)**:
  - **164 Total Quizzes**: Covering Italian ministerial programs for scuole medie and superiori
  - **9 Subjects**: Matematica, Italiano, Storia, Scienze, Inglese, Geografia, Fisica, Filosofia, Latino
  - **Grade Levels**: Separate quiz sets for 'medie' (middle school) and 'superiori' (high school)
  - **Learning Tracks**: Support for liceo scientifico, classico, linguistico, artistico, tecnico, professionale
  - **Curriculum Standards**: Each quiz tagged with ministerial curriculum alignment
  - **Adaptive Selection**: Quiz difficulty adapts based on student performance history
  - **Weak Topic Targeting**: 80% priority to topics where student struggles
- **Enhanced Chatbot-Gamification Integration (December 2025)**:
  - Chatbot interactions automatically update user streak (_update_streak method)
  - Challenge progress tracking for 'chatbot_interazioni' objectives
  - Automatic XP rewards when challenges are completed through chat
  - Full gamification context (rank, XP, streak) in personalized AI responses
  - ChallengeManagerV2 integration for real-time challenge progress updates
- **Unified Messaging System Cleanup (December 2025)**: Consolidated messaging system with cleaner architecture:
  - **Templates Cleanup**: Removed redundant chat.html (93KB) and chat_modern.html (25KB), keeping unified chat_hub.html and chat_room.html
  - **Demo Route Updated**: Demo chat now uses the unified chat_hub.html template
  - **File Reduction**: From 4 chat templates to 2 clean, maintainable templates
- **3D Orbital Online Indicator (December 2025)**: Advanced CSS 3D animated presence system:
  - **Orbiting Particles**: Three concentric rings with glowing particles rotating in 3D space around online users
  - **Real-time Presence**: Socket.IO integration for instant online/offline status updates
  - **Color-coded Particles**: Green (success), cyan (primary), and purple (secondary) glowing orbs
  - **Presence Dot**: Fallback indicator with pulsing animation for online status
  - **Socket Events**: Added `request_online_users`, `user_connected`, `user_disconnected` events with user_id
  - **Online Counter Badge**: Shows live count of online users in the messaging hub
  - **CSS Animations**: `orbit-rotate` (3D rotation), `particle-glow` (scale pulse), `presence-pulse` (glow effect)
  - **Files**: static/css/futuristic-chat.css (3D indicator styles), routes/socket_routes.py (presence events)
- **Futuristic Messaging UI (December 2025)**: Complete redesign of messaging system with cyberpunk aesthetic:
  - **Glassmorphism Design**: Frosted glass panels with backdrop blur effects
  - **Neon Glow Effects**: Cyan, purple, and pink accent colors with CSS glow shadows
  - **Dark Cyberpunk Theme**: Deep space background with grid overlay and radial gradients
  - **Animated Elements**: Float animations, slide-in transitions, pulse effects on badges
  - **Chat Hub**: Quantum-themed conversation list with section dividers and hover effects
  - **Chat Room**: Real-time messaging with typing indicators, scroll-to-bottom button, participants sidebar
  - **Message Bubbles**: Gradient backgrounds for own messages, glass panels for others
  - **Responsive Design**: Mobile-optimized with touch-friendly button sizes
  - **Files**: static/css/futuristic-chat.css, templates/chat_hub.html, templates/chat_room.html
- **Autoscale Deployment Fixes (December 2025)**:
  - **Health Check Endpoints**: Added lightweight `/healthz`, `/health`, and `/ready` endpoints that return 200 immediately (~46ms) without database operations
  - **Root Endpoint Fast Path**: Added health check detection on `/` route - HEAD requests and GoogleHC/kube-probe User-Agents return 200 in <6ms without database queries
  - **Database Migration Safety**: Added `safe_alter_table()` method with PostgreSQL savepoints to prevent "current transaction is aborted" errors during schema migrations; all ALTER TABLE operations now use this method
  - **Redis Configuration**: Changed from hardcoded localhost:6379 to REDIS_URL environment variable; falls back to database-backed session storage when Redis is not configured
  - **Gunicorn Optimization**: Reduced timeout from 180s to 30s, keepalive from 10s to 5s for Autoscale compatibility
  - **Files**: routes/health_routes.py, services/database/database_manager.py, services/auth_service.py, services/school/school_system.py, gunicorn.conf.py, main.py

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
-   **google-genai**: Google Gemini 3.0 API for AI tutoring
-   **Font Awesome**: Icon library
-   **Google Fonts (Inter)**: Typography
-   **Chart.js**: Data visualization
-   **Gunicorn**: WSGI HTTP server
-   **python-dotenv**: Environment variable management
-   **eventlet**: Asynchronous networking