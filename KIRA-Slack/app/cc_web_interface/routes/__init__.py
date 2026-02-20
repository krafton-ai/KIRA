"""
Web Interface Routes
Collection of all route modules
"""

from app.cc_web_interface.routes.auth import router as auth_router
from app.cc_web_interface.routes.bot_auth import router as bot_auth_router
from app.cc_web_interface.routes.meeting import router as meeting_router
from app.cc_web_interface.routes.voice import router as voice_router
from app.cc_web_interface.routes.api import router as api_router

__all__ = [
    "auth_router",
    "bot_auth_router",
    "meeting_router",
    "voice_router",
    "api_router"
]