---
name: deploy
description: Deploying to staging/production via GitHub Actions + AWS SAM, including adding new environment variables.
triggers:
  - "deploy"
  - "staging"
  - "production"
  - "release"
  - "SAM"
edges:
  - target: context/setup.md
    condition: for what each environment variable does
  - target: context/architecture.md
    condition: for the Lambda + API Gateway shape being deployed
last_updated: 2026-07-09
---

# Deploy

## Context

The app ships as one Lambda (FastAPI via Mangum) behind API Gateway, provisioned by AWS SAM. Deploys run in GitHub Actions — `.github/workflows/deploy_to_staging.yml` and `.github/workflows/deploy_to_prod.yml` — using `templates/staging.yaml` and `templates/prod.yaml`. There is no manual AWS-console step.

## Steps

1. Merge to the branch each workflow triggers on (check the `on:` block in the workflow files — staging and prod trigger differently).
2. Watch the Actions run; SAM builds and deploys the stack.
3. Smoke-test: hit `/` and one real report URL on the deployed host (staging: reports-staging.avantifellows.org, prod: reports.avantifellows.org).

## Task: Add a new environment variable

### Steps
1. Add it to `.env.example` (placeholder only, no real value) and your `.env.local`.
2. Add it to the `Environment: Variables:` section of **both** `templates/staging.yaml` and `templates/prod.yaml` (as a parameter if the value differs per env).
3. Add the secret to the GitHub repo settings and thread it through **both** workflow files.
4. Deploy staging first and confirm the Lambda sees the var before touching prod.

### Gotchas
- Vars exist in three places (SAM template, workflow, GH secrets) — missing any one means the Lambda silently gets an empty value.
- SAM parameter names can differ from the env var name (e.g. parameter `HtmlToPdfUrl` → env `HTML_TO_PDF_SERVER_URL`); match the template's mapping, not the name you expect.
- Import-time vars (`PORTAL_BACKEND_URL`) crash the Lambda on cold start if missing — that shows up as API Gateway 502s, not application errors.

## Verify

- [ ] Actions run green
- [ ] `GET /` on the deployed URL returns the hello message
- [ ] One report URL renders; `?format=pdf` streams a PDF
- [ ] CloudWatch logs show no import errors on cold start

## Debug

- 502 from API Gateway → Lambda crashed at import; check CloudWatch for the traceback (usually a missing env var)
- Works on staging, fails on prod → diff the two SAM templates' env sections

## Update Scaffold

- [ ] Update `context/setup.md` env var list when adding/removing vars
- [ ] Update `.mex/ROUTER.md` project state after infra changes
