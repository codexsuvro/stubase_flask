# StuBase Management API

**An enterprise-oriented Student Management System backend built with Flask and PostgreSQL.**

StuBase Management API is a modular, RESTful backend application designed to manage academic and administrative operations within an educational institution.

The project follows a layered architecture with a focus on maintainability, data integrity, authentication, role-based access control, validation and scalable API development.

It is being developed with industry-oriented backend engineering practices rather than as a basic CRUD application.

---

## Key Features

### Authentication & Security
- JWT-based authentication using access and refresh tokens.
- Secure password hashing.
- Role-based access control (RBAC).
- User identity and profile management.
- Token revocation using a database-backed token blocklist.
- Password change with token invalidation.
- Validation of active and verified user accounts.

### Academic & Administrative Management
- Student management.
- Faculty management.
- Department management.
- Head of Department (HOD) management.
- Course management.
- Student course enrollment.
- Attendance management.
- Assessment management.
- Academic results management.
- Role-based administrative operations.

### API Engineering
- RESTful API design.
- UUID-based primary keys.
- Centralized request and response schemas.
- Pagination and query-based filtering.
- Structured validation and error handling.
- Database migrations and schema versioning.
- OpenAPI 3.0.3 documentation.
- Interactive Swagger UI.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python 3.11+ |
| Backend Framework | Flask 3.x |
| Database | PostgreSQL 17 |
| ORM | Flask-SQLAlchemy, SQLAlchemy 2.x |
| Database Migrations | Flask-Migrate, Alembic |
| API Documentation | Flask-Smorest, OpenAPI 3.0.3, Swagger UI |
| Authentication | Flask-JWT-Extended |
| Validation | Marshmallow |
| Security | Bcrypt / Password Hashing |
| Database Driver | Psycopg 3 |
| Environment Management | Python Dotenv |
| API Testing | Postman |
| Automated Testing | Pytest |

---

## Architecture

The application follows a modular, layered architecture that separates HTTP request handling, validation, business logic and database operations.

```text
Client / Postman / Swagger UI
              |
              v
       Flask Application
              |
              v
        API Routes
              |
              v
        Schemas Layer
              |
              v
        Service Layer
              |
              v
       Repository Layer
              |
              v
        SQLAlchemy ORM
              |
              v
         PostgreSQL
```

### Architectural Responsibilities

| Layer | Responsibility |
|---|---|
| Routes | Handles HTTP requests, responses and endpoint-level authorization. |
| Schemas | Validates incoming payloads and structures API responses. |
| Services | Implements business rules and application workflows. |
| Repositories | Handles database queries and persistence operations. |
| Models | Defines entities, relationships and database constraints. |

The application uses Flask's Application Factory Pattern to initialize extensions, register API modules and configure application-level services.

---

## Project Structure

```text
stubase_flask/
│
├── app/
│   │
│   ├── auth/
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── permissions.py
│   │
│   ├── users/
│   ├── departments/
│   ├── courses/
│   ├── enrollments/
│   ├── attendance/
│   ├── assessments/
│   ├── results/
│   ├── dashboard/
│   │
│   ├── models/
│   ├── seeds/
│   ├── utils/
│   │
│   ├── config.py
│   ├── extensions.py
│   └── __init__.py
│
├── migrations/
│
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

Each functional module maintains its own responsibilities and can evolve independently.

---

## Authentication & Authorization

The application uses JSON Web Tokens (JWT) to authenticate users and protect secured API endpoints.

### Supported Roles

| Role | Access |
|---|---|
| ADMIN | Administrative operations and system-wide management. |
| FACULTY | Faculty-specific academic operations and assigned courses. |
| STUDENT | Student-specific operations. |

### Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Authenticate a user and generate JWT tokens. |
| POST | `/auth/refresh` | Generate a new access token using a refresh token. |
| GET | `/auth/me` | Retrieve the authenticated user's profile. |
| POST | `/auth/logout` | Revoke access and refresh tokens. |
| POST | `/auth/change-password` | Change the authenticated user's password. |
| GET | `/auth/admin-check` | Verify ADMIN-level authorization. |

### Security Implementation

- Short-lived access tokens and longer-lived refresh tokens.
- Database-backed token revocation.
- Token versioning to invalidate previously issued tokens after password changes.
- Authorization checks against current user roles.
- Rejection of revoked tokens and inactive or unverified accounts.

---

## Database Design

The application uses PostgreSQL as its relational database.

Database design follows a structured relational approach with UUID-based primary keys and explicit entity relationships.

### Core Entities

- User
- Role
- Student
- Faculty
- Department
- Course
- Enrollment
- Attendance
- Assessment
- Results
- Token Blocklist

### Database Engineering Practices

- UUID-based primary keys.
- Foreign key relationships.
- SQLAlchemy ORM-based persistence.
- Created and updated timestamps.
- Database migrations through Alembic.
- Transaction management and rollback handling.
- Data integrity and uniqueness constraints.

---

## API Documentation

Interactive API documentation is available through Swagger UI.

Once the application is running, access:

```text
http://localhost:5000/swagger-ui
```

OpenAPI specification:

```text
http://localhost:5000/openapi.json
```

Swagger UI supports endpoint discovery, request payload inspection, response visualization and testing of API operations.

---

## Getting Started

### Prerequisites

Ensure the following are installed:

- Python 3.11 or later
- PostgreSQL 17
- Git
- Postman (optional, for API testing)

### 1. Clone the Repository

```bash
git clone https://github.com/codexsuvro/stubase_flask.git

cd stubase_flask
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

SQLALCHEMY_DATABASE_URI=postgresql+psycopg://postgres:your_password@localhost:5432/stubase_management
```

Replace the database credentials with your local PostgreSQL configuration.

**Important:** Use strong, unique secrets and never commit your `.env` file to version control.

### 5. Run Database Migrations

```bash
flask --app run.py db upgrade
```

This applies the existing database migration history.

### 6. Seed Initial Data

```bash
flask --app run.py seed
```

The seed command initializes the predefined roles:

- ADMIN
- FACULTY
- STUDENT

It also creates an initial administrator account if one does not already exist.

Development seed credentials:

```text
Email: admin@stubase.com
Password: Admin@123
```

Change the development password immediately and do not use these credentials in a production environment.

### 7. Start the Application

```bash
python run.py
```

The application will be available at:

```text
http://localhost:5000
```

---

## Testing

The API is tested using Postman and automated tests using Pytest.

Current validation and negative-test coverage includes:

| Test Scenario | Expected HTTP Status |
|---|---:|
| Duplicate assessment creation | 409 Conflict |
| Assessment linked to a nonexistent course | 404 Not Found |
| Academic semester mismatch | 422 Unprocessable Entity |
| Passing marks exceeding maximum marks | 422 Unprocessable Entity |
| Empty PATCH request | 422 Unprocessable Entity |

The assessment validation scenarios above have been successfully verified.

Run the automated test suite using:

```bash
pytest
```

---

## Development Status

StuBase is actively under development. The following represents the current implementation status.

| Component | Status |
|---|---|
| Application factory and configuration | Implemented |
| PostgreSQL integration | Implemented |
| UUID-based database models | Implemented |
| Alembic migrations | Implemented |
| Role and administrator seeding | Implemented |
| JWT authentication | Implemented |
| Token refresh and revocation | Implemented |
| Password management | Implemented |
| Role-based authorization foundation | Implemented |
| Student and faculty management | In development |
| Department and HOD management | In development |
| Course and enrollment management | In development |
| Attendance management | In development |
| Assessment CRUD, pagination and filtering | Implemented |
| Results management | In development |
| Dashboard APIs | In development |
| API validation and error handling | Implemented in developed modules |
| Automated test coverage | In progress |
| Deployment and CI/CD | Planned |

*Implementation status refers to the current development state, not necessarily complete production readiness.*

---

## Engineering Practices

The project emphasizes the following software engineering principles:

- Separation of concerns through layered architecture.
- Modular and reusable application components.
- Database normalization and relational integrity.
- Secure authentication and authorization.
- Consistent API response contracts.
- Input validation and meaningful HTTP status codes.
- Transaction-safe database operations.
- Version-controlled database migrations.
- Maintainable and extensible code organization.

---

## Future Enhancements

Planned improvements include:

- Complete academic program and semester management.
- Enhanced student enrollment and attendance workflows.
- Advanced faculty and HOD assignment management.
- Comprehensive academic results processing.
- Fine-grained permission management.
- Audit logging and administrative activity tracking.
- Advanced dashboards and reporting.
- Expanded automated testing and integration testing.
- Docker-based containerization.
- CI/CD pipeline implementation.
- Cloud deployment and production monitoring.

---

## Project Information

**Project:** StuBase Management API  
**Repository:** [codexsuvro/stubase_flask](https://github.com/codexsuvro/stubase_flask)  
**Backend:** Python / Flask  
**Database:** PostgreSQL  
**Architecture:** Modular Layered Architecture  
**API Standard:** REST  
**Documentation:** OpenAPI / Swagger UI

---

*StuBase Management API is a personal backend engineering project focused on applying enterprise-oriented software development practices to a real-world academic management domain.*
