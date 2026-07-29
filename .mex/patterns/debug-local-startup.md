---
name: debug-local-startup
description: Diagnosing the server failing to start or crashing at import time (env vars, credentials, working directory).
triggers:
  - "won't start"
  - "KeyError"
  - "startup crash"
  - "uvicorn error"
edges:
  - target: context/setup.md
    condition: for the full env var list and setup steps
  - target: context/auth.md
    condition: when the failure is the PORTAL_BACKEND_URL import-time read
last_updated: 2026-07-09
---

# Debug Local Startup

## Context

`app/main.py` does heavy work at import: initializes DynamoDB, Mongo, and BigQuery clients, constructs `SessionsDB` (Firestore client from decoded credentials), and imports the auth module (which reads `PORTAL_BACKEND_URL` from `os.environ` immediately). Most startup failures are env/credential problems, not code.

## Steps

1. Confirm you're running from the right place: `cd app && uv run uvicorn main:app --port 5050 --reload`.
2. Read the traceback bottom-up and match it to the import chain in `main.py`.
3. Check `.env.local` exists at the repo root and includes **all** of: the four `DYNAMODB_*` vars, `MONGO_AUTH_CREDENTIALS`, `FIRESTORE_CREDENTIALS` (base64), `BQ_CREDENTIALS_SECRET_NAME`, `PORTAL_BACKEND_URL`.
4. AWS Secrets Manager access (for BigQuery creds) uses ambient AWS credentials — check `aws sts get-caller-identity` works.

## Gotchas — failure signatures

- `KeyError: 'PORTAL_BACKEND_URL'` → var missing from `.env.local` (it's not in `.env.example`). The load order that makes it work: `main.py` imports `internal.db` (which calls `load_dotenv("../.env.local")`) *before* the router that pulls in `auth` — don't reorder imports in `main.py`.
- `binascii.Error` / `json.JSONDecodeError` in `sessions_db.py` → `FIRESTORE_CREDENTIALS` isn't base64-encoded JSON.
- `botocore.exceptions.ClientError` (Secrets Manager) at startup → `BQ_CREDENTIALS_SECRET_NAME` wrong or no AWS credentials with access to the secret.
- `RuntimeError: Directory 'static' does not exist` or `TemplateNotFound` → uvicorn launched from repo root instead of `app/`.
- `ServerSelectionTimeoutError` (pymongo) on first request → `MONGO_AUTH_CREDENTIALS` wrong or IP not on the Atlas allowlist.

## Verify

- [ ] Server boots with no traceback and `GET /` returns the hello message
- [ ] `/docs` loads and lists all `/reports/*` routes

## Update Scaffold

- [ ] Add any new failure signature you hit to this file
