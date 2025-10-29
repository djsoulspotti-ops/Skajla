## 🎯 **SKAILA MVC + ORM Migration Guide**

This guide shows how to migrate SKAILA from `db_manager` (raw SQL) to **SQLAlchemy ORM** following **MVC pattern** and **professional error handling**.

---

## ✅ **Example Implementation: Courses Module**

I've created a **complete reference implementation** in the `core/` directory:

### **Structure Created:**

```
core/
├── config/
│   ├── database.py           # SQLAlchemy setup with connection pooling
│   └── logging_config.py     # Professional logging with colors
├── exceptions/
│   └── __init__.py           # Custom exceptions (8 types)
├── models/
│   └── course.py             # ORM Model with validation
├── controllers/
│   └── course_controller.py  # Business logic layer
└── (routes/)
    └── courses_routes.py     # Views/Routes layer (in routes/ folder)
```

---

## 📚 **Pattern Components**

### **1. Model (M) - ORM Definition**

**File:** `core/models/course.py`

```python
from sqlalchemy import Column, Integer, String, DateTime
from core.config.database import Base

class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    scuola_id = Column(Integer, nullable=False)
    # ... other fields
    
    def to_dict(self):
        """Serialize to JSON"""
        return {'id': self.id, 'nome': self.nome, ...}
    
    @classmethod
    def validate_data(cls, data: dict):
        """Validate before create/update"""
        if not data.get('nome'):
            return False, "Name required"
        return True, None
```

**✅ Benefits:**
- Type-safe database operations
- Automatic schema management
- Built-in validation
- Relationships support

---

### **2. Controller (C) - Business Logic**

**File:** `core/controllers/course_controller.py`

```python
from core.models.course import Course
from core.config.database import get_db_session
from core.exceptions import ValidationError, ResourceNotFoundError

class CourseController:
    @staticmethod
    def create_course(data: dict) -> Course:
        """Create with validation and error handling"""
        # Validate
        is_valid, error = Course.validate_data(data)
        if not is_valid:
            raise ValidationError(error, context={'data': data})
        
        # Create using ORM
        with get_db_session() as session:
            course = Course(nome=data['nome'], ...)
            session.add(course)
            session.flush()
            
            logger.info(f"Course created: {course.id}")
            return course
    
    @staticmethod
    def get_course_by_id(course_id: int) -> Course:
        """Retrieve with specific error handling"""
        with get_db_session() as session:
            course = session.query(Course).filter(
                Course.id == course_id
            ).first()
            
            if not course:
                raise ResourceNotFoundError(
                    f"Course {course_id} not found",
                    context={'course_id': course_id}
                )
            
            return course
```

**✅ Benefits:**
- Separation of concerns
- Testable business logic
- Specific error handling
- Detailed logging

---

### **3. View (V) - Routes/Presentation**

**File:** `routes/courses_routes.py`

```python
from flask import Blueprint, jsonify, request
from core.controllers.course_controller import CourseController
from core.exceptions import ValidationError, ResourceNotFoundError

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/api/courses', methods=['POST'])
@require_auth
def api_create_course():
    """Thin route - delegates to controller"""
    try:
        data = request.get_json()
        course = CourseController.create_course(data)
        
        return jsonify({
            'success': True,
            'data': course.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': e.message,
            'context': e.context
        }), 400
    except ResourceNotFoundError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 404
```

**✅ Benefits:**
- Thin routes (just HTTP handling)
- Consistent error responses
- Proper HTTP status codes
- Context in errors

---

## 🔄 **Migration Steps for Existing Code**

### **Step 1: Create ORM Model**

**Before (db_manager):**
```python
# Table created with raw SQL
db_manager.execute('''
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100),
        email VARCHAR(100)
    )
''')
```

**After (ORM):**
```python
# core/models/user.py
from sqlalchemy import Column, Integer, String
from core.config.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    email = Column(String(100))
```

---

### **Step 2: Create Controller**

**Before (inline query in route):**
```python
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    db_manager.execute('''
        INSERT INTO users (nome, email) 
        VALUES (%s, %s)
    ''', (data['nome'], data['email']))
    return jsonify({'success': True})
```

**After (Controller + ORM):**
```python
# core/controllers/user_controller.py
class UserController:
    @staticmethod
    def create_user(data: dict) -> User:
        with get_db_session() as session:
            user = User(nome=data['nome'], email=data['email'])
            session.add(user)
            session.flush()
            return user

# routes/users_routes.py
@users_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        user = UserController.create_user(data)
        return jsonify({'success': True, 'data': user.to_dict()}), 201
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
```

---

### **Step 3: Update Route**

**Before (error handling):**
```python
except Exception as e:
    print("Error creating user")  # ❌ Generic
    return jsonify({'error': 'Error'}), 500
```

**After (specific errors):**
```python
except ValidationError as e:
    logger.warning(f"Validation failed: {e.message}")
    return jsonify({
        'error': 'Validation Error',
        'message': e.message,
        'context': e.context
    }), 400
except DatabaseOperationError as e:
    logger.error(f"DB error: {e.message}")
    return jsonify({
        'error': 'Database Error',
        'message': 'Operation failed'
    }), 500
```

---

## 📊 **Comparison Table**

| Aspect | Before (db_manager) | After (ORM + MVC) |
|--------|---------------------|-------------------|
| **Query Style** | Raw SQL `%s` | ORM methods `.query()` |
| **Type Safety** | ❌ None | ✅ SQLAlchemy types |
| **Validation** | Manual in routes | ✅ Model validation |
| **Error Handling** | Generic `Exception` | ✅ Custom exceptions |
| **Logging** | `print()` statements | ✅ Structured logging |
| **Testability** | ❌ Hard (DB dependent) | ✅ Easy (mock session) |
| **Maintainability** | ❌ Queries scattered | ✅ Centralized in controllers |

---

## 🚀 **How to Use the Example**

### **1. Test the Courses API**

```bash
# Create a course
curl -X POST http://localhost:5000/api/courses \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Matematica Avanzata",
    "descrizione": "Corso di calcolo differenziale",
    "scuola_id": 1,
    "anno_scolastico": "2024-2025",
    "professore_id": 5
  }'

# Get course by ID
curl http://localhost:5000/api/courses/1

# Get all courses for a school
curl http://localhost:5000/api/courses/school/1

# Update course
curl -X PUT http://localhost:5000/api/courses/1 \
  -H "Content-Type: application/json" \
  -d '{"descrizione": "Updated description"}'

# Delete course (soft delete)
curl -X DELETE http://localhost:5000/api/courses/1
```

### **2. Check Logs**

You'll see **professional logging**:
```
2025-01-29 14:30:15 - CourseController - INFO - Course created successfully (Context: course_id=1, nome=Matematica, scuola_id=1)
2025-01-29 14:30:20 - CourseController - WARNING - Duplicate course creation attempted (Context: nome=Matematica, scuola_id=1)
2025-01-29 14:30:25 - CourseController - ERROR - Database error creating course (Context: error=IntegrityError, data={...})
```

---

## 📝 **Migration Priority**

Migrate modules in this order:

1. ✅ **Courses** (Example already done)
2. **Users/Auth** - High usage
3. **Classes** - Core functionality
4. **Messaging** - Complex queries
5. **Gamification** - Many operations
6. **Registro** - Teacher operations

---

## 🎓 **Best Practices Applied**

✅ **Separation of Concerns:** Model/Controller/View clearly separated
✅ **ORM Usage:** Zero raw SQL, all operations via SQLAlchemy
✅ **Error Handling:** Specific exceptions with context
✅ **Logging:** Structured logs with levels (DEBUG/INFO/WARNING/ERROR)
✅ **Validation:** Data validated before DB operations
✅ **Type Hints:** All functions have type annotations
✅ **Docstrings:** Every class/method documented
✅ **Single Responsibility:** Each class has one job
✅ **Transaction Management:** Automatic rollback on errors
✅ **Context Managers:** Safe session handling

---

## 🔗 **Next Steps**

1. **Review the example code** in `core/` directory
2. **Test the Courses API** endpoints
3. **Create similar structure** for your next module
4. **Gradually migrate** existing routes
5. **Update** `main.py` to register `courses_bp`

---

## ❓ **Questions?**

The example demonstrates:
- How to define ORM models
- How to create controllers
- How to handle errors properly
- How to log operations
- How to structure routes

Copy this pattern for all new features! 🎯
