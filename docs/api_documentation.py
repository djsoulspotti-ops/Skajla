"""
SKAILA API Documentation Configuration
Swagger/OpenAPI documentation for all REST API endpoints
"""

from flasgger import Swagger

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

# API documentation template
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "SKAILA API Documentation",
        "description": "Complete API documentation for SKAILA Educational Platform",
        "contact": {
            "name": "SKAILA Support",
            "email": "support@skaila.app"
        },
        "version": "1.0.0"
    },
    "host": "0.0.0.0:5000",
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "securityDefinitions": {
        "SessionAuth": {
            "type": "apiKey",
            "name": "session",
            "in": "cookie",
            "description": "Session-based authentication using Flask sessions"
        }
    },
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and registration"
        },
        {
            "name": "User Management",
            "description": "User profile and account management"
        },
        {
            "name": "Gamification",
            "description": "XP, levels, badges, and rewards"
        },
        {
            "name": "Messaging",
            "description": "Real-time chat and messaging"
        },
        {
            "name": "AI Coach",
            "description": "AI-powered learning assistance"
        },
        {
            "name": "Registro Elettronico",
            "description": "Grades, attendance, and class management"
        },
        {
            "name": "Analytics",
            "description": "Performance analytics and reports"
        },
        {
            "name": "School Management",
            "description": "School, class, and teacher administration"
        }
    ]
}

def init_swagger(app):
    """Initialize Swagger documentation"""
    return Swagger(app, config=swagger_config, template=swagger_template)
