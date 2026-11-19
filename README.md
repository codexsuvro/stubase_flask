# StuBase Management API

**An enterprise-oriented Student Management System backend built with Flask and PostgreSQL.**

StuBase is a modular, RESTful backend application designed to manage academic and administrative operations within an educational institution.

The project focuses on practical backend engineering concepts, including layered architecture, secure authentication, role-based access control, relational database design, transaction management, API validation, database integrity, and maintainable application development.

Rather than being a basic CRUD application, StuBase is being developed as an enterprise-oriented academic management platform with an emphasis on real-world business rules, data consistency, and scalable backend architecture.

---

## Table of Contents

- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Authentication and Authorization](#authentication-and-authorization)
- [Database Design](#database-design)
- [Implemented Modules](#implemented-modules)
- [API Documentation](#api-documentation)
- [Getting Started](#getting-started)
- [API Testing and Validation](#api-testing-and-validation)
- [Development Progress](#development-progress)
- [Engineering Practices](#engineering-practices)
- [Roadmap](#roadmap)
- [Project Information](#project-information)

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

- Student and faculty management.
- Department and HOD management.
- Course and enrollment management.
- Academic year and semester management.
- Course offerings.
- Attendance management.
- Assessment and academic result management.
- Academic calendar validation.
- Student and faculty dashboards.

### 3. Assignment Management

- Assignment creation and management.
- Student assignment submissions.
- PDF-only assignment submission and resubmission.
- Private Cloudflare R2 object storage.
- Authorization-checked PDF downloads.
- Temporary signed download URLs.
- Assignment grading workflows.

### 4. Curriculum and Syllabus Management

- Versioned curriculum management.
- Department and academic-year mapping.
- Course-to-curriculum assignment.
- Semester-wise course sequencing.
- Syllabus versioning and lifecycle management.
- Syllabus units and topics.
- Learning outcomes.
- Topic-to-learning-outcome mapping.
- Curriculum and syllabus publishing and archiving.
- Cross-entity validation and data integrity checks.

### 5. Academic Records

- Assessment and result management.
- Student transcript generation.
- JSON and PDF transcript output.
- Academic progress and dashboard information.

### 6. API Engineering

- RESTful API architecture.
- UUID-based primary keys.
- Layered application architecture.
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
| Object Storage | Cloudflare R2 |
| API Testing | Swagger UI, Thunder Client / Postman |
| Version Control | Git, GitHub |

---

## System Architecture

StuBase follows a modular, layered architecture that separates request handling, validation, business logic, and database operations.

### Architecture Overview

```text
                  API Consumers
             (Swagger / Thunder Client)
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

              Assignment PDF Storage
                       |
                       v
                 Cloudflare R2
```

### Architectural Responsibilities

| Layer | Responsibility |
|---|---|
| Routes | HTTP request handling and endpoint authorization |
| Schemas | Request validation and response serialization |
| Services | Business rules and application workflows |
| Repositories | Database queries and persistence operations |
| Models | Entity definitions, relationships, and constraints |

The application uses Flask's Application Factory Pattern to initialize extensions, register API modules, and manage application configuration.

---

## Project Structure

The application is organized into independent functional modules.

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
│   ├── assignments/
│   ├── transcripts/
│   ├── curricula/
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
├── .env
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

*This is a representative structure; individual module files and supporting packages may evolve during development.*

---

## Authentication and Authorization

StuBase uses JSON Web Tokens (JWT) to authenticate users and secure protected endpoints.

### Supported Roles

| Role | Access |
|---|---|
| ADMIN | Administrative operations and system-wide management |
| FACULTY | Faculty-specific academic operations |
| STUDENT | Student-specific academic operations |

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
- Environment-based secret management.

---

## Database Design

PostgreSQL is used as the primary relational database.

The database design follows a structured relational approach with UUID-based primary keys, explicit foreign-key relationships, and database-level integrity constraints.

### Core Entities

- User
- Role
- Student
- Faculty
- Department
- Course
- AcademicYear
- Semester
- CourseOffering
- Enrollment
- Attendance
- Assessment
- Result
- Assignment
- AssignmentSubmission
- Curriculum
- CurriculumCourse
- Syllabus
- SyllabusUnit
- SyllabusTopic
- LearningOutcome
- TopicLearningOutcome
- Token Blocklist

### Database Engineering Practices

- UUID-based primary keys.
- Foreign-key relationships and referential integrity.
- SQLAlchemy ORM-based persistence.
- Created and updated timestamps.
- Database migrations through Alembic.
- Transaction management and rollback handling.
- Unique constraints and data integrity validation.
- Database-level check constraints.
- Indexed foreign-key and frequently queried columns.

---

## Implemented Modules

The following modules have been implemented as part of the current development roadmap.

| Module | Implementation |
|---|---|
| Authentication and Security | Implemented |
| User and Role Management | Implemented |
| Department and HOD Management | Implemented |
| Student and Faculty Management | Implemented |
| Academic Year and Semester Management | Implemented |
| Course Management | Implemented |
| Course Offerings | Implemented |
| Student Enrollment | Implemented |
| Attendance Management | Implemented |
| Assessment Management | Implemented |
| Academic Results | Implemented |
| Academic Calendar Validation | Implemented |
| Student and Faculty Dashboards | Implemented |
| Assignment Management | Implemented |
| Assignment Submission and Grading | Implemented |
| Assignment PDF Storage | Implemented |
| Student Transcripts (JSON/PDF) | Implemented |
| Curriculum Management | Implemented |
| Syllabus Management | Implemented |

### Curriculum and Syllabus Management

The curriculum module supports versioned academic curricula mapped to departments and academic years.

Its syllabus hierarchy supports:

```text
Curriculum
    |
    v
Curriculum Courses
    |
    v
Syllabus Versions
    |
    v
Syllabus Units
    |
    v
Syllabus Topics

Syllabus
    |
    v
Learning Outcomes
    |
    v
Topic-Learning Outcome Mapping
```

The module includes lifecycle management, publishing validations, duplicate prevention, cross-entity validation, and database integrity constraints.

### Assignment PDF Storage

Assignment PDF files are stored in a private Cloudflare R2 bucket rather than directly in PostgreSQL.

Implemented capabilities include:

- PDF-only new submissions and resubmissions.
- Private object storage.
- File-size validation.
- Authorization-checked download endpoints.
- Temporary signed download URLs.
- Preservation of legacy text submission data.

The current application configuration sets a maximum PDF size of 2 MiB.

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
- Postman or Thunder Client (recommended)

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
SECRET_KEY=your-flask-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

SQLALCHEMY_DATABASE_URI=postgresql+psycopg://postgres:your_password@localhost:5432/stubase_management

R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_BUCKET_NAME=stubase-assignment-submissions
```

Replace the placeholders with your own credentials.

**Important security practices:**

- Generate strong, unique Flask and JWT secrets.
- Never commit `.env` to version control.
- Keep Cloudflare R2 credentials private.
- URL-encode special characters in the PostgreSQL password when necessary.
- Use a private R2 bucket with appropriately scoped API credentials.

### 5. Create the Database

Create a PostgreSQL database named:

```sql
CREATE DATABASE stubase_management;
```

Make sure the database credentials in `.env` match your local PostgreSQL configuration.

### 6. Run Database Migrations

```bash
flask --app run.py db upgrade
```

This applies the existing Alembic migration history to the configured database.

### 7. Seed Initial Data

```bash
flask --app run.py seed
```

The seed command initializes the predefined application roles:

- ADMIN
- FACULTY
- STUDENT

It also initializes the development administrator account if one does not already exist.

Use only development credentials locally. Change the initial administrator password immediately.

### 8. Start the Application

```bash
python run.py
```

The application will be available at:

```text
http://localhost:5000
```

Open Swagger UI to explore and test the available APIs.

---

## API Testing and Validation

API endpoints are manually tested using Swagger UI and Thunder Client / Postman.

The validation approach includes:

- Positive API scenarios.
- Negative validation scenarios.
- Authentication and authorization checks.
- Role-based access control verification.
- Duplicate-resource handling.
- Invalid UUID and missing-resource handling.
- Database integrity checks.
- Lifecycle and state-transition validation.
- Verification that failed requests do not leave unintended database changes.

### Verified Assessment Scenarios

| Test Scenario | Expected HTTP Status |
|---|---|
| Duplicate assessment creation | 409 Conflict |
| Assessment linked to a nonexistent course | 404 Not Found |
| Academic semester mismatch | 422 Unprocessable Entity |
| Passing marks exceeding maximum marks | 422 Unprocessable Entity |
| Empty PATCH request | 422 Unprocessable Entity |

### Curriculum Module Validation

The Curriculum and Syllabus module underwent a dedicated manual API validation walkthrough.

- 32 route-method combinations were exercised.
- 50 negative validation scenarios passed.
- Duplicate and invalid resource operations were checked.
- RBAC restrictions were verified.
- Database state was checked before and after failed requests.
- All seven curriculum-related tables were verified after cleanup.
- Foreign keys, constraints, indexes, and migration status were inspected directly in PostgreSQL.

Manual API testing is the current validation approach. Automated test infrastructure is not yet part of the implemented workflow.

---

## Development Progress

StuBase is actively under development.

| Component | Status |
|---|---|
| Application Factory and Configuration | Implemented |
| PostgreSQL Integration | Implemented |
| UUID-based Database Models | Implemented |
| Alembic Database Migrations | Implemented |
| Role and Administrator Seeding | Implemented |
| JWT Authentication | Implemented |
| Token Refresh and Revocation | Implemented |
| Password Management | Implemented |
| Role-Based Authorization | Implemented |
| Academic Management Modules | Implemented |
| Assignment and Submission Management | Implemented |
| Cloudflare R2 Integration | Implemented |
| Transcript JSON/PDF Generation | Implemented |
| Curriculum and Syllabus Management | Implemented |
| Timetable and Conflict Detection | Implemented |
| Course Prerequisites | Implemented |
| Waitlist Management | Implemented |
| Advanced Grading and GPA | Implemented |
| Faculty Workload Management | Implemented |
| Notifications and Announcements | Planned |
| Fees and Scholarship Management | Planned |
| Messaging and Guardian Access | Planned |
| Advanced Analytics and Reporting | Planned |
| Docker and Infrastructure | Planned |
| CI/CD and Deployment | Planned |

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
- Referential integrity and database-level constraints.
- Manual positive, negative, and RBAC API validation.
- Maintainable and extensible code organization.

---

## Roadmap

The next development phases focus on expanding the academic and administrative capabilities of StuBase.

### Academic Scheduling

- Timetable management.
- Faculty scheduling conflict detection.
- Classroom and room conflict detection.
- Student timetable conflict detection.

### Academic Rules and Progression

- Course prerequisites.
- Course waitlists.
- Advanced grading schemes.
- Letter grades, GPA, and CGPA.
- Faculty workload management.

### Administrative Operations

- Notifications and announcements.
- Fee management.
- Scholarships.
- Invoices, payments, and outstanding dues.
- Financial reports.

### Communication and Access

- Basic messaging.
- iCalendar support.
- Restricted guardian access.

### Analytics and Reporting

- Academic KPIs.
- Data exports.
- Explainable dropout-risk indicators.
- Scheduled reports.

### Infrastructure and Engineering

- Docker and Docker Compose.
- Redis integration.
- Celery background jobs.
- MinIO/S3-compatible storage improvements.
- Health and readiness endpoints.
- Rate limiting and caching.
- Structured logging and request IDs.
- Error monitoring and metrics.
- Ruff, Black, mypy, and pre-commit.
- GitHub Actions CI/CD.
- Load testing.
- Cloud deployment and production monitoring.
- Automated testing infrastructure in a later engineering phase.

---

## Project Information

| Attribute | Details |
|---|---|
| Project | StuBase Management API |
| Repository | [codexsuvro/stubase_flask](https://github.com/codexsuvro/stubase_flask) |
| Backend | Python / Flask |
| Database | PostgreSQL |
| Storage | Cloudflare R2 |
| Architecture | Modular Layered Architecture |
| API Standard | REST |
| Documentation | OpenAPI / Swagger UI |
| Project Type | Backend Engineering Project |

---

**StuBase Management API** is a personal backend engineering project focused on building a realistic academic management system while applying industry-oriented backend development, database engineering, security, API design, and software architecture practices.
