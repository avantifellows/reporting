# Reporting Engine

Welcome to the Avanti Fellows Reporting Engine!

## Setting up the Reporting Engine locally

Make sure Python 3.11+ is installed in your system

1. Get everything running with:

```bash
docker-compose up --build
```

2. [ONLY FIRST TIME] Create an external docker volume to enable DynamoDB data to persist between sessions

```bash
docker volume create --name=dynamodb_data
```

3. [ONLY FIRST TIME] Go into the shell of the `app` container and run:

```
python generate_table
```

This will create the the `student_quiz_reports` table.

### Accessing things

DynamoDB Admin: localhost:8001

Reporting FastAPI Server: localhost:5050 (docs and API tryout at localhost:5050/docs)

DynamoDB server: localhost:8000 (we won't access this directly)


## Local Setup Without Docker

### Prerequisites
- Python 3.11+ installed
- [uv](https://docs.astral.sh/uv/) package manager installed

### Setup Steps

1. **Install dependencies and create virtual environment**
```bash
uv sync
```

2. **Install pre-commit hooks**
```bash
uv run pre-commit install
```

3. **Create environment file**
```bash
cp .env.example .env.local
```

4. **Configure credentials**
Obtain credentials from repository owners and replace the local keys in the `.env.local` file.

5. **Run the FastAPI server**
```bash
uv run uvicorn app.main:app --port 5050 --reload
```

The application will be available at `localhost:5050/docs`

### Development Commands

**Update dependencies:**
```bash
uv sync --upgrade
```

**Run code quality checks:**
```bash
uv run pre-commit run --all-files
```

**Add new dependency:**
```bash
uv add <package-name>
```

**Add development dependency:**
```bash
uv add --dev <package-name>
```
## Deployment
We deploy our FastAPI instance on AWS Lambda which is triggered via an API Gateway. In order to automate the process, we use AWS SAM, which creates the stack required for deployment and updates it as needed with just a couple of commands and without having to do anything manually on the AWS GUI. Refer to this [blog](https://www.eliasbrange.dev/posts/deploy-fastapi-on-aws-part-1-lambda-api-gateway/) post for more details.

The actual deployment happens through Github Actions. Look at `.github/workflows/deploy_to_staging.yml` to understand the deployment to Staging and `.github/workflows/deploy_to_prod.yml` for Production.

The details of the AWS Lambda instances are described in `templates/prod.yaml` and `templates/staging.yaml`.
