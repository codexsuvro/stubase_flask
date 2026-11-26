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
- [API Testing](#api-testing)
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

### 6. Notifications and Announcements

- Global and course-offering announcements.
- Draft, publish, and archive lifecycle.
- Role- and enrollment-scoped visibility.
- In-app notification inbox and unread counts.
- Durable email delivery queue with retry tracking.

### 7. Finance

- Versioned fee structures by department and semester, optionally scoped to a course offering.
- Draft editing, activation, archival, and currency-aware fee components.
- Idempotent application to enrolled students with immutable charge snapshots and audited voiding.

### 8. API Engineering

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
│   ├── academic_calendar/
│   ├── course_offerings/
│   ├── timetable/
│   ├── course_prerequisites/
│   ├── waitlists/
│   ├── grading/
│   ├── faculty_workload/
│   ├── assignments/
│   ├── curricula/
│   ├── notifications/
│   ├── announcements/
│   ├── finance/
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
- Announcement
- Notification
- NotificationDelivery
- FeeStructure
- FeeStructureItem
- StudentFeeCharge
- FeeAdjustment
- FeeInvoice
- FeeInvoiceLine
- ScholarshipProgram
- ScholarshipApplication
- ScholarshipApplicationDocument
- ScholarshipAward
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
| Timetable and Scheduling | Implemented |
| Course Prerequisites and Waitlists | Implemented |
| Grading, GPA/CGPA, and Transcripts | Implemented |
| Faculty Workload Tracking | Implemented |
| Notifications and Announcements | Implemented |
| Versioned Fee Structures | Implemented |

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

### Notifications and Announcements

Announcements can be created as drafts, published to a global audience or a
specific course offering, and archived. Administrators can publish global
announcements; faculty can manage announcements for their assigned offerings.
Students see course announcements only while enrolled in the offering.

Publishing creates in-app notifications for active recipients and queues email
deliveries for verified accounts. Email delivery uses a durable database queue
with retries; configure SMTP settings and run the dispatcher with:

```bash
flask --app run.py dispatch-notification-emails --limit 50
```

The dispatcher can be run manually or scheduled. It can later be invoked by
Celery without changing the notification API.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/notifications/me` | List the authenticated user's notifications |
| GET | `/notifications/me/unread-count` | Get unread notification count |
| PATCH | `/notifications/{notification_id}/read` | Mark one notification as read |
| PATCH | `/notifications/me/read-all` | Mark all notifications as read |
| GET | `/announcements` | List announcements visible to the authenticated user |
| POST | `/announcements` | Create a draft announcement |
| GET/PATCH | `/announcements/{announcement_id}` | Get an announcement or update a draft |
| POST | `/announcements/{announcement_id}/publish` | Publish and notify recipients |
| POST | `/announcements/{announcement_id}/archive` | Archive an announcement |

### Finance: Fee Structures

Administrators can define versioned fee schedules for a department and
semester, optionally narrowed to a course offering. Each structure contains
currency-aware fee components. Drafts are editable; activated versions are
immutable, and only one version of a fee code can be active for the same
scope. Archive an active version before activating its replacement. The
additive schema references existing academic tables and does not alter them.
Charges retain their original amount; scholarships and concessions are
recorded as separate auditable adjustments that determine the remaining
balance.

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/finance/fee-structures` | List fee structures or create a draft |
| GET/PATCH | `/finance/fee-structures/{fee_structure_id}` | Get details or update a draft |
| POST | `/finance/fee-structures/{fee_structure_id}/activate` | Activate a draft |
| POST | `/finance/fee-structures/{fee_structure_id}/archive` | Archive without deleting history |

Applying an active schedule snapshots its components as open charges for
students enrolled in the matching department and semester, or the selected
offering. Reapplying is idempotent. Students can view only their own charges;
administrators can list and void charges with an audit reason.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/finance/fee-structures/{fee_structure_id}/apply` | Apply an active schedule to eligible students |
| GET | `/finance/charges` | Admin list of charges with filters |
| GET | `/finance/charges/me` | Student list of their own charges |
| POST | `/finance/charges/{charge_id}/void` | Void a charge with an audit reason |

### Finance: Invoices

Administrators issue an invoice from selected open charges for one student,
semester, and currency. Invoice lines preserve the charge description, original
amount, applied credits, and amount due at issue time. Active invoices prevent
their charges from being voided or having adjustments changed; void the
invoice first to reopen those operations. Voided invoices and their private
PDFs remain available for audit. Students can access only their own invoices.
An invoice is a bill, not proof of payment; payment confirmation is recorded
separately as a receipt.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/finance/invoices` | Admin issues an invoice for 1-100 selected charges |
| GET | `/finance/invoices` | Admin lists invoices with filters |
| GET | `/finance/invoices/me` | Student lists their own invoices |
| GET | `/finance/invoices/{invoice_id}` | Get an invoice, with owner checks |
| GET | `/finance/invoices/{invoice_id}/pdf` | Download the private invoice PDF |
| POST | `/finance/invoices/{invoice_id}/void` | Void an invoice with an audit reason |

### Finance: Manual Payments and Receipts

Administrators record offline payments against issued invoices; this module
does not initiate or verify payments with a gateway. Partial payments are
allowed, overpayments are rejected, and paid/outstanding balances are derived
from the payment ledger. Each recorded payment creates an immutable receipt
snapshot and a private PDF under the existing R2 bucket's
`finance/receipts/` object-key prefix. Students can view their own payment
history and download their receipts. Invoices with recorded payments cannot
be voided. Razorpay, refunds/reversals, dues, and late fees remain separate
future work.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/finance/invoices/{invoice_id}/payments` | Admin records a payment and generates its receipt |
| GET | `/finance/invoices/{invoice_id}/payments` | Admin or owning student lists invoice payments |
| GET | `/finance/payments` | Admin lists payments with filters |
| GET | `/finance/payments/me` | Student lists their own payments |
| GET | `/finance/payments/{payment_id}/receipt` | Admin or owning student downloads the private receipt PDF |

### Scholarships and Concessions

Administrators create and publish scholarship programs for an academic year,
optionally scoped to a semester and department. Programs may specify a minimum
CGPA, application window, fixed or percentage award, recipient or budget
limits, and an optional percentage cap. Students can view programs for which
they meet the published enrollment and CGPA requirements, apply once, and
withdraw while the application is pending. Administrators review applications
and record approved awards or rejection reasons. Approved awards are applied
to matching open charges as separate fee adjustments; original charges are not
overwritten. Administrators may also grant direct concessions against an open
charge. Applicants may attach up to five private PDF supporting documents
(2 MiB each). All
adjustments can be voided with an audit reason; voiding a charge also voids its
active adjustments so the balance and award allocation remain consistent.

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/scholarships/programs` | Admin list/create programs |
| GET/PATCH | `/scholarships/programs/{program_id}` | Get/update a draft program |
| GET | `/scholarships/programs/open` | Student list of eligible open programs |
| POST | `/scholarships/programs/{program_id}/open` | Open applications |
| POST | `/scholarships/programs/{program_id}/close` | Close applications |
| POST | `/scholarships/programs/{program_id}/archive` | Archive a closed program |
| POST | `/scholarships/programs/{program_id}/applications` | Student submits application |
| GET | `/scholarships/applications/me` | Student list of own applications |
| GET | `/scholarships/applications` | Admin list/review queue |
| GET | `/scholarships/applications/{application_id}` | Get own application or admin review |
| POST | `/scholarships/applications/{application_id}/documents` | Student uploads a supporting PDF |
| GET | `/scholarships/applications/{application_id}/documents` | List document metadata |
| GET | `/scholarships/applications/{application_id}/documents/{document_id}` | Download via short-lived private URL |
| POST | `/scholarships/applications/{application_id}/withdraw` | Student withdraws a pending application |
| POST | `/scholarships/applications/{application_id}/approve` | Admin approves and sets award value |
| POST | `/scholarships/applications/{application_id}/reject` | Admin rejects with a reason |
| GET | `/scholarships/awards/me` | Student list of own awards |
| GET | `/scholarships/awards` | Admin list of awards |
| POST | `/scholarships/awards/{award_id}/apply` | Apply an award to eligible open charges |
| POST | `/scholarships/awards/{award_id}/revoke` | Revoke award and void its active adjustments |
| POST | `/scholarships/concessions` | Admin grants a direct concession |
| GET | `/scholarships/adjustments` | Admin lists scholarship/concession credits |
| POST | `/scholarships/adjustments/{adjustment_id}/void` | Admin voids a credit with a reason |

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

MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-smtp-username
MAIL_PASSWORD=your-smtp-password
MAIL_USE_TLS=true
MAIL_FROM_ADDRESS=notifications@example.com
MAIL_FROM_NAME=StuBase
```

Replace the database credentials with your local PostgreSQL configuration.
SMTP settings are required only when dispatching queued email notifications.
Keep SMTP credentials in the local `.env` file or deployment secret store; do
not commit them.
Assignment PDFs are uploaded to a private Cloudflare R2 bucket. R2 uses the
S3-compatible endpoint derived from `R2_ACCOUNT_ID`; set `R2_ENDPOINT_URL`
instead if using a custom endpoint. The PDF upload limit is 2 MiB. The
application returns a temporary, authorization-checked download redirect.
Create the bucket as private and use an R2 API token scoped to that bucket with
object read/write permissions.

**Security:** Use strong, unique secrets. Never commit your `.env` file or production credentials to version control.

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

## API Testing

API endpoints are manually validated using Postman. The automated Pytest
suite is planned after feature development is complete.

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
| Notifications and announcements | Implemented |
| Versioned fee structures and student charge snapshots | Implemented |
| Scholarship applications, awards, and auditable concessions | Implemented |
| Immutable invoice snapshots and private invoice PDFs | Implemented |
| Manual payment recording and receipt PDFs | Implemented |
| Dues, late fees, and financial reports | Pending |
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
- Referential integrity and database-level constraints.
- Manual positive, negative, and RBAC API validation.
- Maintainable and extensible code organization.

---

## Roadmap

Remaining work is planned in these phases:

1. Institutional operations: dues and late fees, then financial reports. Fee
   structures, scholarships, concessions, invoices, manual payments, and
   receipt PDFs are implemented. Payment gateways remain later work.
   Notifications and announcements are implemented.
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
| Storage | Cloudflare R2 |
| Architecture | Modular Layered Architecture |
| API Standard | REST |
| Documentation | OpenAPI / Swagger UI |
| Project Type | Backend Engineering Project |

---

**StuBase Management API** is a personal backend engineering project focused on building a realistic academic management system while applying industry-oriented backend development, database engineering, security, API design, and software architecture practices.
