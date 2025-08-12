# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Avanti Fellows Reporting Engine - a FastAPI-based web application that generates student quiz reports, live session reports, and form responses. The application integrates with multiple data sources (DynamoDB, MongoDB, BigQuery) to provide comprehensive reporting capabilities for educational assessments.

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

# Run the FastAPI server (from project root)
uv run uvicorn app.main:app --port 5050 --reload
```

### Development Commands
```bash
# Update dependencies
uv sync --upgrade

# Add new dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Run code quality checks
uv run pre-commit run --all-files

# Run specific pre-commit hooks
uv run pre-commit run black
uv run pre-commit run flake8
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
- **FormResponsesRouter** (`app/routers/form_responses.py`): Handles form response reports and data visualization

**Database Initialization** (`app/internal/db.py`)
- Initializes connections to DynamoDB, MongoDB, and BigQuery
- Handles environment-specific configuration loading
- Supports both local (.env.local) and production (environment variables) configuration

### Application Architecture

The application follows a layered architecture:
- **Router Layer**: FastAPI routers handle HTTP requests and responses
- **Database Layer**: Database-specific classes abstract data access (DynamoDB, MongoDB, BigQuery)
- **Service Layer**: Business logic for report generation and data processing
- **Template Layer**: Jinja2 templates for HTML report rendering
- **Utility Layer**: PDF conversion, data formatting, and helper functions

### Data Models

**Student Quiz Reports** (`app/models/student_quiz_reports.py`)
- Primary key: session_id, user_id-section
- GSI: user_id for retrieving all reports for a student
- Contains performance metrics by section and chapter-wise breakdown
- Note: Models are documentation-only (not used at runtime)

### Report Types

1. **Student Quiz Reports**: Individual student performance across sections with chapter-wise analysis
2. **Live Session Reports**: Real-time statistics for quiz sessions including participation metrics
3. **Student Reports Summary**: List of all reports for a specific student
4. **Form Responses**: Form submission reports with data visualization

### PDF Generation

The application supports PDF generation for reports using the `utils/pdf_converter.py` module:
- Reports can be accessed with `?format=pdf` parameter
- Uses external HTML-to-PDF service (URL configured via `HtmlToPdfUrl` environment variable)
- Supports debug mode (`?debug=true`) to return HTML instead of PDF

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

The application requires these environment variables (see `.env.example`):

**Database Configuration**
- `DYNAMODB_URL`, `DYNAMODB_REGION`, `DYNAMODB_ACCESS_KEY`, `DYNAMODB_SECRET_KEY`
- `DYNAMODB_STUDENT_REPORTS_TABLE_NAME`: DynamoDB table name
- `MONGO_AUTH_CREDENTIALS`: MongoDB connection string
- `FIRESTORE_CREDENTIALS`: Firestore configuration (if using)
- `BQ_CREDENTIALS_SECRET_NAME`: AWS Secrets Manager secret name for BigQuery credentials

**Service Configuration**
- `HTML_TO_PDF_URL`: External service URL for PDF generation (deployment only)

## Deployment

The application deploys to AWS Lambda using AWS SAM (Serverless Application Model):
- **Staging**: `.github/workflows/deploy_to_staging.yml`
- **Production**: `.github/workflows/deploy_to_prod.yml`
- **SAM Templates**: `templates/staging.yaml` and `templates/prod.yaml`
- **Lambda Runtime**: Python 3.11 with Mangum ASGI adapter
- **Infrastructure**: API Gateway + Lambda + DynamoDB/MongoDB/BigQuery integrations

### Deployment Architecture
- **API Gateway**: Routes HTTP requests to Lambda function
- **Lambda Function**: Runs FastAPI application via Mangum adapter
- **Static Assets**: Served from Lambda (CSS, favicon, etc.)
- **Environment-specific**: Different configurations for staging/production

## Key Features

- **Multi-database Integration**: Seamlessly integrates DynamoDB, MongoDB, and BigQuery
- **Chapter-wise Performance Analysis**: Detailed breakdown with priority ordering
- **Qualification Status Tracking**: BigQuery integration for student recommendations
- **PDF Report Generation**: HTML-to-PDF conversion with debug mode support
- **Live Session Monitoring**: Real-time statistics and day-wise participation metrics
- **Cross-platform Quiz Integration**: Supports different quiz engines and formats
- **Responsive Templates**: Mobile-friendly HTML reports with Jinja2 templating
- **CORS Support**: Configured for Gurukul and other frontend integrations
