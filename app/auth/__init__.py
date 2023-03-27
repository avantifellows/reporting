import httpx
from fastapi import Request, HTTPException, status

# Portal Backend URL
VERIFICATION_URL = "https://9nqmv8p8k2.execute-api.ap-south-1.amazonaws.com/auth/verify"


async def verify_token(request: Request) -> bool:
    # This function will be used to verify the bearer token
    auth_header = request.headers.get("Authorization")
    bearer_prefix = "Bearer "

    if not auth_header or not auth_header.startswith(bearer_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[len(bearer_prefix) :]
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(VERIFICATION_URL, headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        if "id" in json_response:
            return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
