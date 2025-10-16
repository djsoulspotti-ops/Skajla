# Overview

SKAILA is an educational platform for schools, offering a multi-role messaging system, an intelligent AI chatbot for personalized tutoring, gamification, and comprehensive analytics. It connects students, teachers, parents, and administrators in real-time. The platform is a Flask web application with Socket.IO for real-time communication, designed to be scalable and specifically tailored for the Italian education system. It aims to enhance learning engagement and provide robust tools for school management.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask with a modular architecture, separating concerns into blueprints for authentication, dashboards, and APIs.

## Database Layer
Supports both SQLite (development) and PostgreSQL (production) with a custom `DatabaseManager` for connection pooling and fallback mechanisms. The schema supports multi-tenant school management, users, chat, gamification, and AI interaction tracking.

## Multi-Tenant School System
SKAILA includes a comprehensive school, class, and teacher management system with dynamic class creation, role-based registration, and automated chat room creation, supporting isolated data for unlimited schools.

## Real-time Communication
Socket.IO provides real-time messaging with automatic reconnection and room-based chat for various chat types (class-based, thematic, administrative).

## AI Integration
A native SKAILA AI system powers personalized learning:
-   **SKAILA AI Brain Engine**: Analyzes student profiles for context, subject detection, sentiment, and prioritizes responses with 8 types of personalized feedback.
-   **Adaptive Quiz System**: Features a multi-subject quiz database (34+ quizzes) that adapts difficulty, focuses on weak topics, and integrates with XP and badge systems.
-   **Social Learning System**: Facilitates peer help matching, study group creation, and awards collaborative XP.
-   **Subject Progress Analytics**: Provides comprehensive overview of student performance, identifies weak areas, generates learning paths, and offers AI-driven suggestions.

## Gamification Engine
Tracks user engagement with XP points, levels, badges, achievements, streak tracking, and performance analytics to motivate learning.

## Performance Optimization
Includes multi-level caching, Redis-backed session management, performance monitoring, and database connection pooling.

## Security Features
Uses bcrypt for password hashing, rate limiting for brute-force prevention, and role-based access control.

## Robust Authentication System (UPDATED - Oct 2025)
SKAILA now features a production-ready, user-friendly authentication system:
-   **Auto-Managed SECRET_KEY**: Automatically generates and persists SECRET_KEY in `.env.secrets` file, eliminating session reset issues. Falls back to Replit Secrets in production.
-   **Remember Me Feature**: Users can choose 30-day persistent sessions (default) or 1-day sessions, improving user experience.
-   **Smart Lockout Protection**: After multiple failed login attempts, users receive accurate countdown messages ("Try again in X minutes") with proper time calculation.
-   **Enhanced Feedback**: Clear error messages for lockout, invalid credentials, and success messages ("👋 Welcome back, [name]!").
-   **Modern UI**: Beautiful purple gradient login page with custom checkbox styling, autocomplete support for password managers, and smooth animations.
-   **Session Persistence**: Sessions no longer reset on server restart thanks to persistent SECRET_KEY storage.

## Modern UI/UX Design (Oct 16, 2025)
SKAILA features a completely redesigned, immersive user interface:
-   **Purple Gradient Background**: Stunning animated gradient (purple to violet) with radial pattern overlays for a premium, modern look
-   **Glass Morphism Design**: Frosted glass effect with backdrop-filter blur for all components
-   **Intelligent Layout**: Grid-based responsive design (2fr 1fr) that adapts to screen sizes
-   **Smooth Animations**: Hover effects, fade-in animations, and transform transitions for premium feel
-   **Removed Clutter**: Eliminated "Azioni Rapide" section for cleaner, more focused experience

## SKAILA Connect - Student Career Portal (Oct 16, 2025)
Revolutionary feature connecting students with real companies for internships and job opportunities:
-   **Company Database**: Structured table with companies, sectors, positions, requirements, and compensation
-   **Smart Application System**: One-click applications with XP rewards (50 XP for first application only)
-   **Anti-Farming Protection**: Duplicate applications detected, XP awarded only for new submissions
-   **API Endpoints**: `/api/skaila-connect/companies`, `/apply`, `/my-applications`
-   **Input Validation**: Complete validation (company existence, active status) with proper error handling
-   **Dynamic UI**: Company cards loaded from database with logo emojis, descriptions, and action buttons
-   **5 Partner Companies**: TechStart Italia, Innovation Lab, Creative Digital, Green Energy Corp, MediaTech Solutions

## Integrated Online Register (Oct 16, 2025)
Complete digital register system replacing obsolete school systems:
-   **Database Tables**: `voti` (grades 1-10 scale), `presenze` (attendance tracking)
-   **Student View**: Tabs for Grades, Attendance, Statistics with responsive design
-   **Grade Tracking**: Subject-wise grades, evaluation types (written/oral), teacher notes
-   **Attendance System**: Daily presence tracking, justified absences, tardiness recording
-   **Statistics Dashboard**: Automated average calculation per subject, visual progress bars, overall performance metrics
-   **Teacher Interface**: Separate view for professors to manage class grades and attendance
-   **Purple Gradient Theme**: Consistent design language across all register pages

## New Features
-   **Teaching Materials Management System**: Allows teachers to upload, organize, and manage various file types (PDF, DOC, images, video) with class-based access control and download analytics.
-   **Electronic Class Register (Registro Elettronico)**: Comprehensive student management including attendance tracking, grade recording (Italian 1-10 scale), disciplinary notes, and a lesson calendar.
-   **AI-Powered Register Intelligence**: Provides a "Student Risk Assessment System" (0-100 score), anomaly detection (grade drops, absence changes), intervention planning, and "Class Health Monitoring."
-   **Parent Communication System**: Generates automated weekly and monthly reports with attendance, grades, behavior updates, homework tracking, and AI insights. It also provides real-time notifications for important events.

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