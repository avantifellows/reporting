# Technical Debt Cleanup TODO

This document outlines critical technical debt that must be addressed before this codebase can be considered production-ready. Items are ordered by priority (P0 = Critical, P1 = High, P2 = Medium).

## P0 - Critical Security Issues (MUST FIX IMMEDIATELY)

### 1. Fix SQL Injection Vulnerability
**File**: `app/db/bq_db.py:18-19`
**Issue**: Using f-strings with user input in SQL queries
**Fix**: Replace with parameterized queries
```python
# Current (VULNERABLE):
query_string = f"WHERE user_id = '{user_id}' AND test_id = '{test_id}'"

# Fix with parameterized query:
query_string = """
    WHERE user_id = @user_id AND test_id = @test_id
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
        bigquery.ScalarQueryParameter("test_id", "STRING", test_id),
    ]
)
```

### 2. Remove Hardcoded API Key
**File**: `app/routers/student_quiz_reports.py:44`
**Issue**: API key hardcoded in source code
**Fix**:
- Move to environment variables
- Add to `.env.example` file
- Update `internal/db.py` to load this credential
```python
# Remove this line:
AF_API_KEY = "6qOO8UdF1EGxLgzwIbQN"

# Add to environment loading:
AF_API_KEY = os.getenv("AF_API_KEY")
```

## P1 - High Priority Architectural Issues

### 3. Implement Dependency Injection Container
**Files**: `app/main.py`, all router classes
**Issue**: Hard-coded dependencies, impossible to test
**Fix**:
- Create `app/core/container.py` with dependency injection
- Use FastAPI's `Depends()` for dependency injection
- Create interfaces for all database classes

### 4. Break Down God Classes
**Files**: `app/routers/student_quiz_reports.py`, `app/routers/session_quiz_reports.py`
**Issue**: Router classes doing too much (400+ line methods)
**Fix**: Extract services:
- Create `app/services/student_report_service.py`
- Create `app/services/session_report_service.py`
- Create `app/services/pdf_service.py`
- Create `app/services/chapter_analysis_service.py`

**Example structure**:
```
app/services/
├── __init__.py
├── student_report_service.py
├── session_report_service.py
├── pdf_service.py
├── chapter_analysis_service.py
└── qualification_service.py
```

### 5. Create Unified Database Abstraction
**Files**: All `app/db/*.py` files
**Issue**: Inconsistent interfaces and error handling across databases
**Fix**: Create repository pattern:
- Create `app/repositories/base_repository.py` with common interface
- Create `app/repositories/student_reports_repository.py`
- Create `app/repositories/quiz_repository.py`
- Create `app/repositories/bigquery_repository.py`
- Implement consistent error handling across all repositories

### 6. Implement Proper Configuration Management
**File**: `app/internal/db.py`
**Issue**: Complex, fragile environment loading
**Fix**:
- Create `app/core/config.py` using Pydantic BaseSettings
- Validate all configuration on startup
- Remove complex conditional environment loading

**Example**:
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    dynamodb_url: str
    dynamodb_region: str
    dynamodb_access_key: str
    dynamodb_secret_key: str
    mongo_auth_credentials: str
    bq_credentials_secret_name: str
    af_api_key: str

    class Config:
        env_file = ".env"
```

## P1 - High Priority Code Quality Issues

### 7. Extract Business Logic from Controllers
**Files**: `app/routers/student_quiz_reports.py` (lines 91-204)
**Issue**: Complex business logic embedded in router methods
**Fix**: Move these functions to service classes:
- `_parse_section_data()` → `StudentReportService.parse_section_data()`
- `_get_chapter_priority_ordering()` → `ChapterAnalysisService.get_priority_ordering()`
- `_get_chapter_for_revision()` → `ChapterAnalysisService.get_revision_recommendation()`

### 8. Add Input Validation
**Files**: All router methods
**Issue**: No input validation, prone to errors
**Fix**: Create Pydantic models for all request/response data:
- Create `app/schemas/student_reports.py`
- Create `app/schemas/session_reports.py`
- Add validation decorators to all endpoints

### 9. Implement Structured Logging
**Files**: All files (currently using print statements)
**Issue**: Using print() for debugging, no structured logging
**Fix**:
- Add `python-json-logger` to requirements
- Create `app/core/logging.py`
- Replace all print statements with proper logging
- Add request ID tracing

### 10. Add Error Handling Middleware
**Files**: `app/main.py`
**Issue**: Inconsistent error handling across endpoints
**Fix**: Create `app/middleware/error_handler.py`
- Catch and format all exceptions consistently
- Add proper HTTP status codes
- Log all errors with context

## P2 - Medium Priority Performance Issues

### 11. Implement Caching Strategy
**Files**: All database operations
**Issue**: No caching, hitting databases for every request
**Fix**:
- Add Redis to docker-compose.yaml
- Create `app/core/cache.py`
- Cache frequently accessed data (student reports, quiz metadata)
- Add cache invalidation strategy

### 12. Add Pagination
**Files**: `app/db/reports_db.py:14-17`
**Issue**: `get_all()` does full table scan
**Fix**:
- Add pagination parameters to all list endpoints
- Implement cursor-based pagination for DynamoDB
- Add limit/offset for other databases

### 13. Optimize Database Queries
**Files**: All database classes
**Issue**: Potential N+1 queries, inefficient data fetching
**Fix**:
- Review all database calls in report generation
- Implement batch fetching where possible
- Add database query monitoring

## P2 - Medium Priority Maintainability Issues

### 14. Extract Constants and Configuration
**Files**: `app/routers/student_quiz_reports.py` (lines 172-173, others)
**Issue**: Magic numbers scattered throughout code
**Fix**: Create `app/core/constants.py`
```python
# Extract these to constants:
ACCURACY_THRESHOLD = 75
ATTEMPT_RATE_THRESHOLD = 50
QUALIFICATION_THRESHOLDS = {
    "JEE_MAINS": 90,
    "JEE_ADVANCED": 120,
    "NEET": 600
}
```

### 15. Standardize Naming Conventions
**Files**: All files
**Issue**: Inconsistent naming (`user_id`, `userId`, `user_id-section`)
**Fix**:
- Create naming convention document
- Standardize all variable names
- Update database schema documentation

### 16. Create API Documentation
**Files**: All router files
**Issue**: No proper API documentation beyond FastAPI auto-generation
**Fix**:
- Add comprehensive docstrings to all endpoints
- Create OpenAPI tags and descriptions
- Add example requests/responses

### 17. Add Health Check Endpoints
**Files**: `app/main.py`
**Issue**: No health monitoring
**Fix**: Add endpoints for:
- `/health` - Basic health check
- `/health/db` - Database connectivity check
- `/health/detailed` - Comprehensive system status

## Implementation Priority Order

1. **Week 1**: Fix P0 security issues (#1, #2)
2. **Week 2**: Implement dependency injection (#3) and configuration management (#6)
3. **Week 3**: Break down god classes (#4) and extract business logic (#7)
4. **Week 4**: Create database abstraction (#5) and add input validation (#8)
5. **Week 5**: Add logging (#9) and error handling (#10)
6. **Week 6+**: Address P2 items based on business priority

## Testing Strategy (Post-Cleanup)

Once the above items are addressed, implement:
- Unit tests for all service classes
- Integration tests for database operations
- End-to-end tests for critical user flows
- Performance tests for report generation

## Success Metrics

- Zero hardcoded credentials in source code
- All database queries use parameterized queries
- Average method length < 20 lines
- Test coverage > 80%
- Response time < 2 seconds for all endpoints
- Zero SQL injection vulnerabilities in security scan
