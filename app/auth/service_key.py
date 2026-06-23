import hmac
import os

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

# Service-to-service auth for trusted callers (e.g. the af_lms backend).
# The end user is authenticated/authorized by the caller; reporting only checks
# that the caller holds the shared secret. Distinct header from the Portal
# `Authorization: Bearer` path so the two never collide.
service_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


def verify_service_key(api_key: str = Security(service_key_header)) -> str:
    """FastAPI dependency: 401 unless X-Api-Key matches REPORTING_SERVICE_API_KEY."""
    expected = os.getenv("REPORTING_SERVICE_API_KEY")
    if not expected:
        # Misconfiguration: fail closed rather than allow everything through.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service key not configured",
        )
    if not api_key or not hmac.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service key",
        )
    return api_key
