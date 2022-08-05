# Reporting Engine

Welcome to the AF Reporting Engine!

## Installation and First Run

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

## Accessing things

DynamoDB Admin: localhost:8001

Reporting FastAPI Server: localhost:5050 (docs and API tryout at localhost:5050/docs)

DynamoDB server: localhost:8000 (we won't access this directly)

