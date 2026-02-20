"""
Meeting Routes
Meeting recording and related functionality routes
"""

import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.cc_slack_handlers import is_authorized_user
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/meeting", tags=["meeting"])


def require_auth(request: Request) -> dict:
    """Check authentication"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/upload")
async def upload_recording(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_auth)
):
    """Upload meeting recording file"""
    try:
        settings = get_settings()

        # Create today's date folder (YYYYMMDD)
        today = datetime.now().strftime("%Y%m%d")
        meetings_dir = Path(settings.FILESYSTEM_BASE_DIR) / "meetings" / today
        meetings_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        contents = await file.read()
        file_path = meetings_dir / file.filename

        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(f"[MEETING] Saved: {file_path}")

        return JSONResponse({
            "status": "success",
            "message": "Meeting recording saved",
            "filename": f"{today}/{file.filename}",
            "user": user.get("name")
        })

    except Exception as e:
        logger.error(f"Failed to upload recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_recordings(request: Request, user: dict = Depends(require_auth)):
    """List meeting recordings"""
    # Query list from database or file system
    return {
        "recordings": [],
        "user": user.get("name")
    }


@router.get("/transcribe/{recording_id}")
async def get_transcription(
    recording_id: str,
    request: Request,
    user: dict = Depends(require_auth)
):
    """Get meeting recording transcription"""
    # Return transcription result
    return {
        "recording_id": recording_id,
        "transcription": "...",
        "user": user.get("name")
    }