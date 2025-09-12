# Overview

SKAILA is a comprehensive educational platform that facilitates communication and learning within school environments. The platform serves as a multi-role messaging system connecting students, teachers, parents, and administrators through a real-time chat interface. It features an intelligent AI chatbot for personalized tutoring, gamification systems to enhance student engagement, and comprehensive analytics for tracking learning progress.

The platform is built as a Flask web application with Socket.IO for real-time communication, supporting scalable user management and educational tools designed specifically for the Italian education system.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
The application uses Flask as the primary web framework with a modular architecture pattern. The main application is structured around separate blueprints for authentication, dashboard, and API routes, promoting clean separation of concerns and maintainability.

## Database Layer
The system implements a flexible database architecture with support for both SQLite (development) and PostgreSQL (production). A custom DatabaseManager class handles connection pooling and provides fallback mechanisms, ensuring scalability for 1000+ concurrent users. The database schema includes comprehensive tables for users, chat rooms, messages, gamification data, AI interaction tracking, and **multi-tenant school management**.

## Multi-Tenant School System
**NEW:** SKAILA now features a comprehensive school-class-teacher management system:
- **School Organization**: Multiple schools with unique codes and teacher invite systems
- **Class Management**: Dynamic class creation and automatic student-teacher associations  
- **Role-Based Registration**: Intelligent registration flow that assigns student/teacher roles based on invite codes
- **Automated Group Creation**: System automatically creates school, class, and teacher chat rooms
- **Scalable Architecture**: Supports unlimited schools with isolated data and communication channels

## Real-time Communication
Socket.IO integration enables real-time messaging functionality with automatic reconnection and room-based chat organization. The system supports multiple chat types including class-based, thematic, and administrative channels.

## AI Integration
The platform features an advanced AI chatbot system built around OpenAI's API with intelligent cost management and response caching. The AI system includes personalized learning profiles, conversation memory, and adaptive response generation based on user roles and learning patterns.

## Gamification Engine
A comprehensive gamification system tracks user engagement through XP points, levels, badges, and achievements. The system includes streak tracking, performance analytics, and reward mechanisms designed to motivate student participation and learning progress.

## Performance Optimization
Multiple performance enhancement systems including:
- Multi-level caching with LRU eviction policies
- Session management with Redis support for scalability
- Performance monitoring for system metrics and response times
- Connection pooling for database operations

## Security Features
The authentication system uses bcrypt for password hashing with fallback support for legacy systems. Rate limiting and attempt tracking prevent brute force attacks, while role-based access control ensures appropriate permissions across different user types.

# External Dependencies

## Core Dependencies
- **Flask**: Web framework for application structure and routing
- **Flask-SocketIO**: Real-time bidirectional communication between clients and server
- **OpenAI API**: Powers the intelligent AI chatbot with natural language processing capabilities
- **bcrypt**: Secure password hashing and verification
- **psutil**: System performance monitoring and resource tracking

## Database Systems
- **SQLite**: Default development database with file-based storage
- **PostgreSQL**: Production database with connection pooling (via psycopg2)
- **Redis**: Optional session storage and caching layer for improved scalability

## Frontend Assets
- **Font Awesome**: Icon library for user interface elements
- **Google Fonts (Inter)**: Typography system for consistent visual design
- **Chart.js**: Data visualization for analytics and gamification dashboards

## Development Tools
- **Gunicorn**: WSGI HTTP server for production deployment
- **python-dotenv**: Environment variable management for configuration
- **eventlet**: Asynchronous networking library for Socket.IO support