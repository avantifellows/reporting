---
name: auth
description: Launch-token verification and the report access model. Load when working on report access control, launch tokens, or the quiz-review handoff.
triggers:
  - "auth"
  - "launch token"
  - "launchToken"
  - "cookie"
  - "401"
  - "verify"
edges:
  - target: context/reports.md
    condition: when the token-resolved user feeds into report lookup
  - target: context/architecture.md
    condition: when the portal backend's place in the system is needed
  - target: patterns/add-report-endpoint.md
    condition: when adding a token-protected endpoint pair
last_updated: 2026-07-09
---

# Auth & Launch Tokens

## Access model

There are two ways into a report:

1. **Direct URL with explicit user_id** (`/reports/student_quiz_report/{session_id}/{user_id}`) — unauthenticated; anyone with the link can view. This is the shareable/legacy path.
2. **Launch-token URL** (`/reports/student_quiz_report/{session_id}?launchToken=...`) — the quiz app or portal appends a token; this service resolves the canonical user from it.

## Launch-token flow

1. Portal/quiz redirects the student to a report URL with `?launchToken=`.
2. The `{session_id}`-only endpoint sees the token and calls `redirect_with_launch_cookie` (`app/utils/report_launch.py`): verifies the token, then 302-redirects to the same path **without** the token in the query string, setting an httponly, samesite=lax cookie scoped to the clean path. Cookie name is `{prefix}_{sanitized_session_id}` (e.g. `student_quiz_report_launch_...`), max age 15 minutes.
3. On the clean request, the token is read back from the cookie, verified again, stored on `request.state.report_launch_token`, and `resolve_report_user_id` extracts `data.user_id` (fallback `payload.id`).
4. The handler then delegates to the plain `{session_id}/{user_id}` endpoint.

Verification (`app/auth/__init__.py`) is a GET to `{PORTAL_BACKEND_URL}/auth/verify` with the token as a Bearer header. A valid launch token must have `data.session_mode == "launch"` and `data.aud == "report"`. Any failure → 401.

## Quiz-review handoff

`_build_quiz_review_link` (in `app/routers/student_quiz_reports.py`) reuses the *same verified token* from `request.state` to build `https://quiz.avantifellows.org/quiz/{quiz_id}?apiKey=...&launchToken=...` — the quiz app resolves identity from the token and strips it from its URL after boot. No token on the request → no review button.

## Cookie prefixes in use

- `student_quiz_report_launch` — v2/v1 report
- `student_quiz_report_v3_launch` — v3 report
- `form_responses_launch` — form responses

## Gotchas

- `PORTAL_BACKEND_URL` is read with `os.environ[...]` **at import time** of `app/auth/__init__.py` — missing var means the whole app crashes on startup, not a 500 on first use. It works locally only because `internal.db` loads `.env.local` before `auth` is imported in `main.py`.
- Token verification is a **synchronous** httpx call (10s timeout) inside request handling — a slow portal backend stalls report loads.
- `verify_token` (Bearer header check) exists alongside `verify_launch_token`; the `api_key_header` dependency on `get_student_reports` is currently decorative (`auto_error=False`, never validated).
- Cookies are set `secure` only when the request scheme is https — locally over http the cookie still works.
