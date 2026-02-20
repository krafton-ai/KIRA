"""
KIRA Web Interface Server
Voice input and web interface server
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Import routers
from app.cc_web_interface.routes import (
    auth_router,
    bot_auth_router,
    meeting_router,
    voice_router,
    api_router
)
from app.cc_web_interface.auth_handler import auth_handler
from app.cc_web_interface.utils import get_session_user, require_auth
from app.cc_slack_handlers import is_authorized_user
from app.cc_utils.slack_helper import get_bot_profile_image

logger = logging.getLogger(__name__)

# Create FastAPI app
web_app = FastAPI(title="KIRA Web Interface")

# Add session middleware
web_app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-this-in-production"  # TODO: Change to environment variable
)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    web_app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Register routers
web_app.include_router(auth_router)
web_app.include_router(bot_auth_router)
web_app.include_router(meeting_router)
web_app.include_router(voice_router)
web_app.include_router(api_router)


@web_app.get("/")
async def home(request: Request):
    """Main page (voice input UI)"""
    # Check login
    user = get_session_user(request)

    if not user:
        # Redirect to login if authentication required
        if require_auth(request):
            return await auth_handler.handle_login(request)
        else:
            # Development mode - set virtual user
            user = {
                'email': 'dev@localhost',
                'name': 'Developer',
                'id': 'dev_user'
            }
            request.session['user'] = user

    # Re-verify if user is authorized
    if not is_authorized_user(user.get('name', '')):
        logger.warning(f"[AUTH] Unauthorized access attempt: {user.get('name')} ({user.get('email')})")
        request.session.clear()
        return HTMLResponse(
            content=f"<h1>Access Denied</h1><p>User: {user.get('name')} ({user.get('email')})</p><p>Please contact the administrator.</p>",
            status_code=403
        )

    # Logged in user: display voice UI
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Replace template variables
        from app.config.settings import get_settings
        settings = get_settings()
        bot_profile_image = get_bot_profile_image()

        html_content = html_content.replace('{{BOT_NAME}}', settings.BOT_NAME)
        html_content = html_content.replace('{{BOT_ORGANIZATION}}', settings.BOT_ORGANIZATION)
        html_content = html_content.replace('{{USER_NAME}}', user.get('name', 'User'))
        html_content = html_content.replace('{{BOT_PROFILE_IMAGE}}', bot_profile_image)
        html_content = html_content.replace('{{CLOVA_ENABLED}}', str(settings.CLOVA_ENABLED).lower())

        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(content="<h1>Voice Interface</h1><p>index.html file not found.</p>")


@web_app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "KIRA Web Interface"}