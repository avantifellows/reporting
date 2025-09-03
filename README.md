# Reporting Engine

Welcome to the Avanti Fellows Reporting Engine!

## Local Setup

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
cd app; uv run uvicorn app.main:app --port 5050 --reload
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
