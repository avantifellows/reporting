from typing import Optional
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from auth import verify_launch_token

REPORT_LAUNCH_COOKIE_MAX_AGE = 15 * 60


def resolve_report_user_id(user_id: Optional[str], launch_token: Optional[str]) -> str:
    if user_id:
        return user_id

    payload = verify_launch_token(launch_token, expected_audience="report")
    token_data = payload.get("data", {})
    canonical_user_id = token_data.get("user_id") or payload.get("id")

    if not canonical_user_id:
        raise HTTPException(status_code=401, detail="Missing user in launch token")

    return str(canonical_user_id)


def get_launch_cookie_name(prefix: str, session_id: str) -> str:
    safe_session_id = "".join(char if char.isalnum() else "_" for char in session_id)
    return f"{prefix}_{safe_session_id}"


def set_launch_cookie(
    response: RedirectResponse,
    request: Request,
    cookie_name: str,
    token: str,
    path: str,
) -> None:
    response.set_cookie(
        key=cookie_name,
        value=token,
        max_age=REPORT_LAUNCH_COOKIE_MAX_AGE,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path=path,
    )


def clean_query_string(request: Request) -> str:
    params = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key != "launchToken"
    ]
    return urlencode(params, doseq=True)


def redirect_with_launch_cookie(
    request: Request,
    session_id: str,
    launch_token: str,
    cookie_prefix: str,
    clean_path: str,
) -> RedirectResponse:
    verify_launch_token(launch_token, expected_audience="report")

    redirect_url = clean_path
    query_string = clean_query_string(request)
    if query_string:
        redirect_url = f"{redirect_url}?{query_string}"

    response = RedirectResponse(url=redirect_url, status_code=302)
    cookie_name = get_launch_cookie_name(cookie_prefix, session_id)
    set_launch_cookie(response, request, cookie_name, launch_token, clean_path)
    return response


def get_report_launch_token(
    request: Request,
    session_id: str,
    launch_token: Optional[str],
    cookie_prefix: str,
) -> str:
    if launch_token:
        return launch_token

    cookie_name = get_launch_cookie_name(cookie_prefix, session_id)
    token = request.cookies.get(cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Missing launch token")
    return token


def set_request_launch_token(request: Request, launch_token: Optional[str]) -> None:
    request.state.report_launch_token = launch_token
