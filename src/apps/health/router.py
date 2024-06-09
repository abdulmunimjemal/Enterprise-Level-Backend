from datetime import datetime, timezone
from fastapi import APIRouter, status
import psutil

from .schemas import APIStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Health check", "model": APIStatus}},
    response_model=APIStatus,
)
async def health_check() -> APIStatus:
    return APIStatus(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        uptime=psutil.boot_time(),
        message="Service is running smoothly",
    )
