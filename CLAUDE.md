# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Avanti Fellows Reporting Engine - a FastAPI-based web application that generates student quiz reports and live session reports. The application integrates with multiple data sources (DynamoDB, MongoDB, BigQuery) to provide comprehensive reporting capabilities for educational assessments.

## Development Setup

### Local Development with uv
```bash
# Install dependencies and create virtual environment
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Copy environment file
cp .env.example .env.local
# (Add actual credentials to .env.local)

# Run the FastAPI server
uv run uvicorn app.main:app --port 5050 --reload
```

### Access Points
- FastAPI Server: http://localhost:5050 (API docs at /docs)

## Code Quality

### Pre-commit Hooks
The repository uses pre-commit hooks for code quality:
- **black**: Python code formatting
- **flake8**: Linting (ignores E501, E203, W503)
- **Standard hooks**: trailing whitespace, JSON/YAML validation, merge conflicts

### Running Code Quality Checks
```bash
# Run pre-commit on all files
uv run pre-commit run --all-files

# Run specific hooks
uv run pre-commit run black
uv run pre-commit run flake8

# Install dependencies (if not already done)
uv sync
```

## Architecture

### Core Components

**FastAPI Application** (`app/main.py`)
- Main application entry point using FastAPI
- Configured with CORS middleware for cross-origin requests
- Uses Mangum adapter for AWS Lambda deployment
- Includes router modules for different report types

**Database Layer**
- **ReportsDB** (`app/db/reports_db.py`): DynamoDB operations for student quiz reports
- **QuizDB** (`app/db/quiz_db.py`): MongoDB operations for quiz data and live statistics
- **BigQueryDB** (`app/db/bq_db.py`): BigQuery operations for qualification data
- **SessionsDB** (`app/db/sessions_db.py`): MongoDB operations for session data

**Router Classes**
- **StudentQuizReportsRouter** (`app/routers/student_quiz_reports.py`): Handles individual student reports, supports PDF generation
- **SessionQuizReportsRouter** (`app/routers/session_quiz_reports.py`): Handles live session reports

**Database Initialization** (`app/internal/db.py`)
- Initializes connections to DynamoDB, MongoDB, and BigQuery
- Handles environment-specific configuration loading

### Data Models

**Student Quiz Reports** (`app/models/student_quiz_reports.py`)
- Primary key: session_id, user_id-section
- GSI: user_id for retrieving all reports for a student
- Contains performance metrics by section and chapter-wise breakdown

### Report Types

1. **Student Quiz Reports**: Individual student performance across sections with chapter-wise analysis
2. **Live Session Reports**: Real-time statistics for quiz sessions including participation metrics
3. **Student Reports Summary**: List of all reports for a specific student

### PDF Generation

The application supports PDF generation for reports using the `utils/pdf_converter.py` module. Reports can be accessed with `?format=pdf` parameter.

## Database Schema

### DynamoDB (student_quiz_reports)
- **Primary Key**: session_id (partition), user_id-section (sort)
- **GSI**: user_id for student-centric queries
- **Attributes**: performance metrics, percentiles, chapter-wise data

### MongoDB Collections
- **quiz.quizzes**: Quiz metadata and configuration
- **quiz.sessions**: User session data and quiz attempts

### BigQuery Tables
- **student_profile_al**: Student qualification status and recommendations

## Environment Variables

Required environment variables:
- `DYNAMODB_URL`, `DYNAMODB_REGION`, `DYNAMODB_ACCESS_KEY`, `DYNAMODB_SECRET_KEY`
- `MONGO_AUTH_CREDENTIALS`
- `BQ_CREDENTIALS_SECRET_NAME`

## Deployment

The application deploys to AWS Lambda via GitHub Actions:
- **Staging**: `.github/workflows/deploy_to_staging.yml`
- **Production**: `.github/workflows/deploy_to_prod.yml`
- **Templates**: `templates/staging.yaml` and `templates/prod.yaml`

## Key Features

- Chapter-wise performance analysis with priority ordering
- Qualification status tracking via BigQuery integration
- PDF report generation with debug capabilities
- Live session monitoring with day-wise statistics
- Cross-platform quiz integration (supports different quiz engines)
- Responsive HTML templates for report viewing
