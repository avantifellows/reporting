# Quiz Reporting Engine

A FastAPI application for generating and serving reports for educational quiz data across multiple platforms.

## Project Overview

This application is a reporting engine that processes quiz data from different sources and generates student performance reports. It connects to multiple databases (DynamoDB, MongoDB, and BigQuery) to retrieve and process data, then serves the reports via API endpoints and HTML templates.

## Features

- Student quiz performance reports
- Session-based quiz reports
- Chapter-wise performance analytics
- Data visualization of student performance
- Integration with quiz platforms

## Tech Stack

- **Framework**: FastAPI
- **Databases**:
  - DynamoDB (reports data)
  - MongoDB (quiz data)
  - BigQuery (analytics data)
- **Deployment**: AWS Lambda (via Mangum adapter)
- **Authentication**: Token-based

## Local Development Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- AWS CLI (for direct DynamoDB access)

### Option 1: Quick Setup with Docker (Recommended)

1. Install pre-commit hooks in the repo
```bash
pip install pre-commit
pre-commit install
```

2. Get everything running with:
```bash
docker-compose up --build
```

3. [ONLY FIRST TIME] Create an external docker volume to enable DynamoDB data to persist between sessions
```bash
docker volume create --name=dynamodb_data
```

4. [ONLY FIRST TIME] Go into the shell of the `app` container and run:
```bash
python generate_table
```

This will create the the `student_quiz_reports` table.

### Accessing Services

- DynamoDB Admin: http://localhost:8001
- Reporting FastAPI Server: http://localhost:5050 (docs and API tryout at http://localhost:5050/docs)
- DynamoDB server: http://localhost:8000 (we won't access this directly)

### Option 2: Direct Setup (Without Docker)

1. Install pre-commit hooks in the repo
```bash
pip install pre-commit
pre-commit install
```

2. Create a `.env.local` file using `.env.example`.
```sh
cp .env.example .env.local
```

3. Obtain credentials to replace local keys in the newly created `.env.local` file from repository owners.

4. Run the following to get app at `localhost:5050/docs`
```bash
cd app; uvicorn main:app --port 5050 --reload
```

### Environment Variables

Create a `.env.local` file in the root directory with the following variables:

```
# DynamoDB
DYNAMODB_URL=http://localhost:8000
DYNAMODB_REGION=us-east-1
DYNAMODB_ACCESS_KEY=your-access-key
DYNAMODB_SECRET_KEY=your-secret-key
DYNAMODB_STUDENT_REPORTS_TABLE_NAME=student_quiz_reports

# MongoDB
MONGO_AUTH_CREDENTIALS=mongodb://localhost:27017/quiz_db

# BigQuery
BQ_CREDENTIALS_SECRET_NAME=your-secret-name
```

## API Documentation

Once the application is running, you can access the automatically generated API documentation at http://localhost:5050/docs. The documentation includes all available endpoints and their request/response schemas.

### Sample Reports

The reporting engine generates various types of interactive reports. Here are some examples:

1. **Standard Student Quiz Report**:
   [Example Student Report](https://reports.avantifellows.org/reports/student_quiz_report/DelhiStudents_6560babef1e8210320907831/20180023021)

2. **V3 Enhanced Report**:
   [Enhanced Student Report - V3](https://reports-staging.avantifellows.org/reports/student_quiz_report/v3/FeedingIndiaStudents_67d53b5e0fcc46bf14d4e2b4/9931967805)

3. **Session-based Report**:
   [Session Report](https://reports-staging.avantifellows.org/reports/student_quiz_report/FeedingIndiaStudents_67d53b5e0fcc46bf14d4e2b4/9931967805)

These reports use the following URL patterns:
- `/reports/student_quiz_report/{session_id}/{user_id}`
- `/reports/student_quiz_report/v3/{session_id}/{user_id}`

## Database Setup

### DynamoDB

The application uses DynamoDB to store reports data. In the development environment, we use DynamoDB Local, which is automatically set up with Docker Compose.

Main tables:
- `student_quiz_reports` - Stores student quiz performance data with chapter-wise analytics

### MongoDB

MongoDB is used to store quiz data. In the development environment, it's set up automatically with Docker Compose.

### BigQuery

BigQuery is used for analytics data. In the development environment, credentials can be provided through AWS Secrets Manager.

## Project Structure

- `/app` - Main application code
  - `/routers` - API endpoints
  - `/db` - Database interaction modules
  - `/models` - Pydantic models for data validation
  - `/templates` - Jinja2 templates for HTML rendering
  - `/static` - Static files (CSS, JavaScript)
  - `/auth` - Authentication modules
  - `/internal` - Internal utilities

## Deployment

We deploy our FastAPI instance on AWS Lambda which is triggered via an API Gateway. In order to automate the process, we use AWS SAM, which creates the stack required for deployment and updates it as needed with just a couple of commands and without having to do anything manually on the AWS GUI. Refer to this [blog](https://www.eliasbrange.dev/posts/deploy-fastapi-on-aws-part-1-lambda-api-gateway/) post for more details.

The actual deployment happens through Github Actions. Look at `.github/workflows/deploy_to_staging.yml` to understand the deployment to Staging and `.github/workflows/deploy_to_prod.yml` for Production.

The details of the AWS Lambda instances are described in `templates/prod.yaml` and `templates/staging.yaml`.

## Development Workflow

To make development easier, the project includes a Makefile with various commands:

```bash
# Run the application locally
make run

# Run tests
make test

# Lint and format code
make lint
make format

# Start Docker services
make docker-up

# Stop Docker services
make docker-down

# Clean up temporary files
make clean

# See all available commands
make help
```

If you prefer to run commands directly:

```bash
# Run the application locally
cd app && uvicorn main:app --port 5050 --reload

# Run tests
cd app && pytest

# Start Docker services
docker-compose up -d

# Stop Docker services
docker-compose down
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more detailed guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
