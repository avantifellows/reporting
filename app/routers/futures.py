from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()


templates = Jinja2Templates(directory="templates")


@router.get("/futures")
async def futures_page(request: Request):
    return templates.TemplateResponse("futures.html", {"request": request})


@router.get("/api/futures/config")
async def get_futures_config():
    """Get futures configuration including API URL"""
    return {
        "futures_api_url": os.getenv(
            "FUTURES_API_URL", "http://localhost:3001/api/predict"
        ),
        "college_predictor_url": os.getenv(
            "COLLEGE_PREDICTOR_URL", "http://localhost:3001"
        ),
    }
