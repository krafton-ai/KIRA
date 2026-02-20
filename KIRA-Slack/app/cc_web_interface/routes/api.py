"""
API Routes
General API endpoints
"""

import logging
from fastapi import APIRouter, Request

from app.cc_web_interface.stt_provider import get_stt_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/config")
async def get_config():
    """Return STT Provider configuration"""
    provider = get_stt_provider()
    return {
        "provider_type": provider.get_provider_type(),
        "config": provider.get_client_config()
    }


@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "KIRA Web Interface"
    }