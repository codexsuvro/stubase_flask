# StuBase Management API

**An enterprise-oriented Student Management System backend built with Flask and PostgreSQL.**

StuBase is a modular, RESTful backend application designed to manage academic and administrative operations within an educational institution.

The project focuses on practical backend engineering concepts, including layered architecture, secure authentication, role-based access control, relational database design, transaction management, API validation, and maintainable application development.

Rather than being a basic CRUD application, StuBase is being developed with industry-oriented software engineering practices and scalable application design in mind.

---

## Table of Contents

- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Authentication and Authorization](#authentication-and-authorization)
- [Database Design](#database-design)
- [API Documentation](#api-documentation)
- [Getting Started](#getting-started)
- [API Testing](#api-testing)
- [Development Progress](#development-progress)
- [Engineering Practices](#engineering-practices)
- [Roadmap](#roadmap)

---

## Key Features

### 1. Authentication and Security
- JWT-based authentication.
- Access and refresh token management.
- Secure password hashing.
- Role-Based Access Control (RBAC).
- Database-backed token revocation.
- Password management and token invalidation.
- Account verification and activation checks.
- Protected API endpoints.

### 2. Academic Management
- Student management.
- Faculty management.
- Department management.
- Head of Department (HOD) management.
- Course management.
- Student course enrollment.
- Attendance management.
- Assessment management.
- Academic results management.

### 3. API Engineering
- RESTful API architecture.
- UUID-based primary keys.
- Centralized request and response validation.
- Pagination and query-based filtering.
- Structured error handling.
- Database migrations and schema versioning.
- OpenAPI 3.0.3 documentation.
- Interactive Swagger UI.

---

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.11+ |
| Backend Framework | Flask 3.x |
| Database | PostgreSQL 17 |
| ORM | Flask-SQLAlchemy |
| Database Migrations | Flask-Migrate, Alembic |
| API Documentation | Flask-Smorest, OpenAPI 3.0.3 |
| API Interface | Swagger UI |
| Authentication | Flask-JWT-Extended |
| Validation | Marshmallow |
| Database Driver | Psycopg 3 |
| Password Security | Bcrypt / Password Hashing |
| Environment Management | Python Dotenv |
| API Testing | Postman |
| Automated Testing | Pytest |

---

## System Architecture

StuBase follows a modular, layered architecture that separates request handling, validation, business logic, and database operations.

### Architecture Overview

```text
             API Consumers
          (Postman / Swagger UI)
                   |
                   v
           Flask Application
                   |
                   v
              API Routes
                   |
                   v
             Schema Layer
          (Marshmallow)
                   |
                   v
             Service Layer
           (Business Logic)
                   |
                   v
           Repository Layer
           (Data Access)
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
| Routes | HTTP request handling and endpoint authorization |
| Schemas | Request validation and response serialization |
| Services | Business rules and application workflows |
| Repositories | Database queries and persistence operations |
| Models | Entity definitions, relationships and constraints |

The application uses Flask's Application Factory Pattern to initialize extensions, register API modules, and manage application configuration.

---

## Project Structure

```text
stubase_flask/
│
├── app/
│   ├── auth/
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
│   └── versions/
│
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

The application is organized around functional modules to maintain separation of concerns and support independent feature development.

---

## Authentication and Authorization

StuBase uses JSON Web Tokens (JWT) to authenticate users and secure protected endpoints.

### Supported Roles

| Role | Access |
|---|---|
| ADMIN | Administrative operations and system-wide management |
| FACULTY | Faculty-specific academic operations |
| STUDENT | Student-specific operations |

### Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Authenticate users and generate JWT tokens |
| POST | `/auth/refresh` | Generate a new access token |
| GET | `/auth/me` | Retrieve the authenticated user's profile |
| POST | `/auth/logout` | Revoke authentication tokens |
| POST | `/auth/change-password` | Change account password |
| GET | `/auth/admin-check` | Verify administrator authorization |

### Security Implementation

- Short-lived access tokens and longer-lived refresh tokens.
- Database-backed token revocation.
- Token versioning for invalidating previously issued tokens.
- Role verification against current user permissions.
- Rejection of revoked tokens and inactive or unverified accounts.
- Secure password storage.

---

## Database Design

PostgreSQL is used as the primary relational database.

The database design follows a structured relational approach with UUID-based primary keys, explicit foreign key relationships, and database-level integrity constraints.

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
- Foreign key relationships and referential integrity.
- SQLAlchemy ORM-based persistence.
- Created and updated timestamps.
- Database migrations through Alembic.
- Transaction management and rollback handling.
- Unique constraints and data integrity validation.

---

## API Documentation

StuBase provides interactive API documentation using Swagger UI and OpenAPI 3.0.3.

Once the application is running, access:

| Resource | URL |
|---|---|
| Swagger UI | http://localhost:5000/swagger-ui |
| OpenAPI Specification | http://localhost:5000/openapi.json |
| API Base URL | http://localhost:5000 |

Swagger UI allows developers to:

- Explore available API endpoints.
- Inspect request and response schemas.
- Understand HTTP status codes.
- Execute API requests.
- Test authenticated endpoints.

---

## Getting Started

### Prerequisites

Make sure the following tools are installed:

- Python 3.11 or later
- PostgreSQL 17
- Git
- Postman (recommended)

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

R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_BUCKET_NAME=your-private-bucket-name
```

Replace the database credentials with your local PostgreSQL configuration.
Assignment PDFs are uploaded to a private Cloudflare R2 bucket. R2 uses the
S3-compatible endpoint derived from `R2_ACCOUNT_ID`; set `R2_ENDPOINT_URL`
instead if using a custom endpoint. The PDF upload limit is 2 MiB. The
application returns a temporary, authorization-checked download redirect.
Create the bucket as private and use an R2 API token scoped to that bucket with
object read/write permissions.

**Security:** Use strong, unique secrets. Never commit your `.env` file or production credentials to version control.

### Assignment PDF submissions

Run the database migration after configuring R2. Student endpoints accept
multipart form data with a `file` field:

- `POST /assignments/{assignment_id}/submissions/pdf` to submit a PDF.
- `PATCH /assignments/submissions/{submission_id}/pdf` to resubmit a PDF when
  the assignment allows resubmissions.
- `GET /assignments/submissions/{submission_id}/pdf` to download it. The API
  authorizes the caller and redirects to a short-lived R2 URL.

New submissions and resubmissions are PDF-only. The legacy `text_response`
column and read-only response field are retained so existing text submissions
remain readable; no migration drops or rewrites that historical data.

### 5. Run Database Migrations

```bash
flask --app run.py db upgrade
```

This applies the existing Alembic migration history to the configured database.

### 6. Seed Initial Data

```bash
flask --app run.py seed
```

The seed command initializes the predefined application roles:

- ADMIN
- FACULTY
- STUDENT

It also initializes the development administrator account if one does not already exist.

Use only development credentials locally. Change the initial administrator password immediately.

### 7. Start the Application

```bash
python run.py
```

The application will be available at:

```text
http://localhost:5000
```

Open Swagger UI to explore and test the available APIs.

---

## API Testing

API endpoints are currently validated using Postman. The automated Pytest suite is planned after feature development is complete.

### Assessment Module Validation

The Assessment module includes CRUD operations, pagination, filtering, and negative-test validation.

Verified validation scenarios include:

| Test Scenario | Expected HTTP Status |
|---|---|
| Duplicate assessment creation | 409 Conflict |
| Assessment linked to a nonexistent course | 404 Not Found |
| Academic semester mismatch | 422 Unprocessable Entity |
| Passing marks exceeding maximum marks | 422 Unprocessable Entity |
| Empty PATCH request | 422 Unprocessable Entity |

Additional negative-test scenarios have also been verified during development.

---

## Development Progress

StuBase is actively under development. The following table reflects the current implementation status.

| Component | Status |
|---|---|
| Authentication, security hardening, and RBAC | Implemented |
| Students, faculty, departments, and courses | Implemented |
| Academic years, semesters, and course offerings | Implemented |
| Enrollments, attendance, assessments, and results | Implemented |
| Role-based dashboards | Implemented |
| Timetable and scheduling conflict checks | Implemented |
| Course prerequisites and waitlists | Implemented |
| Grading, GPA/CGPA, and transcript PDFs | Implemented |
| Faculty workload tracking | Implemented |
| Assignments and PDF submissions using Cloudflare R2 | Implemented |
| Curriculum and syllabus management | Implemented |
| Notifications and announcements | Pending |
| Fees, concessions, invoices, dues, and financial reports | Pending |
| Advanced analytics, at-risk insights, and ML prediction | Pending |
| Docker, background jobs, health checks, and production infrastructure | Pending |
| Automated test suite | Planned after feature development |
| CI/CD, observability, load testing, and deployment | Pending |

*Implementation status reflects ongoing development and does not indicate complete production readiness.*

---

## Engineering Practices

The project emphasizes practical software engineering principles:

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

## Roadmap

Remaining work is planned in these phases:

1. Institutional operations: notifications, announcements, and finance.
2. Analytics: dashboard KPI extensions, exports, at-risk analysis, and dropout-risk prediction.
3. Production infrastructure: Docker, Redis/Celery, health checks, caching, rate limiting, and environment configuration.
4. Engineering quality and delivery: automated tests after feature development, CI/CD, observability, load testing, and deployment.

---

## Project Information

| Attribute | Details |
|---|---|
| Project | StuBase Management API |
| Repository | [codexsuvro/stubase_flask](https://github.com/codexsuvro/stubase_flask) |
| Backend | Python / Flask |
| Database | PostgreSQL |
| Architecture | Modular Layered Architecture |
| API Standard | REST |
| Documentation | OpenAPI / Swagger UI |
| Project Type | Backend Engineering Project |

---

**StuBase Management API** is a personal backend engineering project focused on building a realistic academic management system while applying industry-oriented backend development, database engineering, security, and API design practices.
