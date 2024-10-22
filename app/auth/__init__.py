import httpx
from fastapi import Request

# Portal Backend URL
VERIFICATION_URL = "https://b93ddkdz0g.execute-api.ap-south-1.amazonaws.com/auth/verify"


async def verify_token(request: Request) -> bool:
    # This function will be used to verify the bearer token
    auth_header = request.headers.get("Authorization")
    bearer_prefix = "Bearer "

    if not auth_header or not auth_header.startswith(bearer_prefix):
        return False  # Invalid or missing token

    token = auth_header[len(bearer_prefix) :]
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(VERIFICATION_URL, headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        if "id" in json_response:
            return True  # Token is valid

    return False  # Invalid token
