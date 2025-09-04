from fastapi import APIRouter

router = APIRouter(prefix="/api/futures", tags=["futures"])


@router.get("/")
async def futures_page():
    """Serve the futures prediction page"""
    return {"message": "JEE Futures Prediction API"}
