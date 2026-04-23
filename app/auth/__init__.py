import os

import httpx
from fastapi import Request, HTTPException, status

PORTAL_BACKEND_BASE_URL = "https://b93ddkdz0g.execute-api.ap-south-1.amazonaws.com"
VERIFICATION_URL = f"{PORTAL_BACKEND_BASE_URL}/auth/verify"


def _verify_token_value(token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(VERIFICATION_URL, headers=headers, timeout=10)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    json_response = response.json()
    if "id" not in json_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return json_response


async def verify_token(request: Request) -> bool:
    auth_header = request.headers.get("Authorization")
    bearer_prefix = "Bearer "

    if not auth_header or not auth_header.startswith(bearer_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[len(bearer_prefix) :]
    _verify_token_value(token)
    return token


def verify_launch_token(token: str, expected_audience: str = "report") -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Missing launch token")

    payload = _verify_token_value(token)
    token_data = payload.get("data", {})

    if token_data.get("session_mode") != "launch":
        raise HTTPException(status_code=401, detail="Invalid launch token")

    token_audience = token_data.get("aud")
    if expected_audience and token_audience != expected_audience:
        raise HTTPException(status_code=401, detail="Invalid launch token audience")

    return payload
