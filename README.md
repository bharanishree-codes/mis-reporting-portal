# MIS Reporting Portal

A scalable, multi-tenant Management Information System (MIS) platform for academic institutions, supporting ETL-driven reporting, role-based dashboards, and dynamic data filtering across departments and academic years.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Django](https://img.shields.io/badge/Django-092E20?logo=django)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?logo=mysql)

## Overview

The MIS Reporting Portal is a multi-tenant platform that gives academic institutions a unified way to manage reporting and administrative data. It supports multiple departments and academic years within a single deployment, with role-specific dashboards for HODs, faculty, and compliance teams, and flexible, database-driven configuration for job scheduling and system adaptability.

## Features

- **Multi-tenant architecture** — supports multiple institutions/departments from a single deployment
- **ETL workflows** — reporting and administrative data integration pipelines
- **Role-based dashboards** — tailored views and permissions for HODs, faculty, and compliance teams
- **Dynamic filtering & reporting** — SQL-based report generation by department and academic year
- **Configurable job scheduling** — database-driven task scheduling and system adaptability across tenants

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django, FastAPI, Django REST Framework (DRF) |
| Database | MySQL |
| Frontend | Bootstrap, JavaScript |
| API Docs | Swagger / OpenAPI |
| Version Control | Git |

## Project Structure

```
MIS/
├── mis_vas1/                     # Core reporting & academic-data module
│   ├── migrations/
│   ├── templates/
│   ├── _templates/
│   ├── admin.py
│   ├── apps.py
│   ├── Faculty.py
│   ├── Faculty_exchange.py
│   ├── books.py
│   ├── Career_counseling.py
│   ├── collaborative_students.py
│   ├── competitive_examination.py
│   ├── Courses_project.py
│   ├── Extentions.py
│   ├── government.py
│   ├── program_offered.py
│   ├── Research.py
│   ├── urls.py
│   └── workshop.py
├── Starter/                      # Django project settings & root config
├── templates/                    # Shared HTML templates
├── user_management/
│   ├── migrations/
│   ├── templates/
│   ├── templatetags/
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── menuelements.py
│   ├── menuprivilege.py
│   ├── models.py
│   ├── rolesmaster.py
│   ├── settings_views.py
│   ├── urls.py
│   ├── user_drf.py              # DRF-based auth/user endpoints
│   ├── usermaster.py
│   ├── userprivilege.py
│   └── views.py
├── config                        # Environment/app configuration
├── manage.py
├── requirement                    # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8.0+
- pip / virtualenv

### Installation

```bash
# Clone the repository
git clone https://github.com/bharanishree-codes/mis-reporting-portal.git
cd mis-reporting-portal

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

## API Documentation

Once the server is running, API documentation is available at:

- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Key Contributions

- Developed a scalable multi-tenant MIS platform with ETL workflows for reporting and administrative data integration
- Implemented RBAC for HODs, faculty, and compliance teams
- Built dynamic filtering and SQL-based report generation by department and academic year
- Integrated database-driven configurations for flexible job scheduling and cross-tenant adaptability

## Contact

**Bharani Shree R**
Email: bharanishree2002.08@gmail.com
LinkedIn: [linkedin.com/in/bharanishree](https://linkedin.com/in/bharanishree)
