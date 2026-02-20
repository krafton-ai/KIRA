import asyncio
import logging
import os
import sys

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# DEBUG: Check environment variables at startup
logging.info(f"[STARTUP DEBUG] CLAUDE_CODE_CLI_PATH={os.environ.get('CLAUDE_CODE_CLI_PATH', 'NOT SET')}")
logging.info(f"[STARTUP DEBUG] PATH={os.environ.get('PATH', 'NOT SET')[:200]}...")
logging.info(f"[STARTUP DEBUG] WEB_INTERFACE_AUTH_PROVIDER={os.environ.get('WEB_INTERFACE_AUTH_PROVIDER', 'NOT SET')}")

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from app.config.settings import get_settings
from app.queueing_extended import start_channel_workers
from app.scheduler import scheduler, reload_schedules_from_file
from app.cc_slack_handlers import _process_message_logic
from app.cc_slack_handlers import register_handlers
from app.cc_utils.waiting_answer_db import init_db
from app.cc_utils.confirm_db import init_db as init_confirm_db
from app.cc_utils.email_tasks_db import init_db as init_email_tasks_db
from app.cc_utils.jira_tasks_db import init_db as init_jira_tasks_db

settings = get_settings()


async def main():
    """Main function to setup and run the Slack bot."""

    # 1. Load settings
    settings = get_settings()

    # 1-1. Chrome profile setup (first-time login or always if enabled)
    if settings.CHROME_ENABLED:
        from pathlib import Path

        profile_dir = Path(settings.FILESYSTEM_BASE_DIR) / "chrome_profile"

        # Open browser if profile doesn't exist or CHROME_ALWAYS_PROFILE_SETUP=True
        should_open_browser = (
            not profile_dir.exists()
            or not any(profile_dir.iterdir())
            or settings.CHROME_ALWAYS_PROFILE_SETUP
        )

        if should_open_browser:
            if settings.CHROME_ALWAYS_PROFILE_SETUP:
                logging.info("[CHROME_SETUP] 🌐 Opening browser for profile setup (CHROME_ALWAYS_PROFILE_SETUP=True)...")
            else:
                logging.info("[CHROME_SETUP] 🌐 Opening browser for initial login...")
            logging.info(
                "[CHROME_SETUP] Please login to any sites you need and press ENTER when done."
            )

            try:
                from playwright.async_api import async_playwright

                async with async_playwright() as p:
                    # Launch Chrome browser (using persistent context)
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=str(profile_dir),
                        channel="chrome",
                        headless=False,
                        # Bot detection bypass settings
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-dev-shm-usage",
                            "--no-sandbox",
                        ],
                        ignore_default_args=["--enable-automation"],
                        bypass_csp=True,
                    )
                    page = await context.new_page()

                    # Open Google
                    await page.goto("https://www.google.com")

                    print("\n" + "=" * 70)
                    print("🌐 Chrome browser opened for profile setup")
                    print("=" * 70)
                    print("\n👉 Log in to any sites you need (Google, etc.)")
                    print("👉 When done, press ENTER to continue...")
                    print("=" * 70 + "\n")

                    # Wait for user input (in separate thread)
                    await asyncio.to_thread(lambda: input("Press ENTER to continue: "))

                    # Close browser
                    await context.close()

                logging.info("[CHROME_SETUP] ✅ Browser closed, login saved!")
            except Exception as e:
                logging.error(f"[CHROME_SETUP] ❌ Failed to setup Chrome: {e}")
        else:
            logging.info("[CHROME_SETUP] Chrome profile already exists, skipping setup")

    # 2. Initialize waiting_answer database
    init_db()
    logging.info("Waiting answer database initialized")

    # 2-1. Initialize confirm database
    init_confirm_db()
    logging.info("Confirm database initialized")

    # 2-2. Initialize email tasks database
    init_email_tasks_db()
    logging.info("Email tasks database initialized")

    # 2-3. Initialize jira tasks database
    init_jira_tasks_db()
    logging.info("Jira tasks database initialized")

    # 3. Validate signing secret
    if not settings.SLACK_SIGNING_SECRET or settings.SLACK_SIGNING_SECRET == "...":
        logging.error(
            "Error: SLACK_SIGNING_SECRET is not set. Please set it in your config/settings.py file."
        )
        sys.exit(1)

    # 3. Initialize Slack AsyncApp
    app = AsyncApp(
        token=settings.SLACK_BOT_TOKEN, signing_secret=settings.SLACK_SIGNING_SECRET
    )

    # 4. Get bot user ID
    try:
        auth_test = await app.client.auth_test()
        bot_user_id = auth_test["user_id"]

        # Set global bot user ID for handlers
        from app.cc_slack_handlers import set_bot_user_id

        set_bot_user_id(bot_user_id)
        logging.info(f"App is running as user: {bot_user_id}")
    except Exception as e:
        logging.error(f"Error checking auth: {e}")
        sys.exit(1)

    # 6. Register handlers
    register_handlers(app)

    # 7-1. Wrap the message process
    async def process_wrapper(message, client):
        await _process_message_logic(message, client)

    # 7-2. Wrap the orchestrator process
    async def orchestrator_wrapper(job, client):
        # Get memory (reuse if already retrieved, otherwise retrieve new)
        retrieved_memory = job.get("retrieved_memory")
        if not retrieved_memory:
            from app.cc_agents.memory_retriever import call_memory_retriever

            logging.info(f"[ORCHESTRATOR_WRAPPER] Retrieving relevant memories...")
            retrieved_memory = await call_memory_retriever(
                query=job["query"],
                slack_data=job["slack_data"],
                message_data=job["message_data"],
            )
            logging.info(
                f"[ORCHESTRATOR_WRAPPER] Memory retrieved: {retrieved_memory[:100] if retrieved_memory else 'None'}..."
            )
        else:
            logging.info(
                f"[ORCHESTRATOR_WRAPPER] Using pre-retrieved memory: {retrieved_memory[:100] if retrieved_memory else 'None'}..."
            )

        # Run Operator
        from app.cc_agents.operator.agent import call_operator_agent

        response = await call_operator_agent(
            user_query=job["query"],
            slack_data=job["slack_data"],
            message_data=job["message_data"],
            retrieved_memory=retrieved_memory,
        )
        logging.info(
            f"[ORCHESTRATOR_WRAPPER] Response: {response[:100] if response else 'None'}..."
        )

    # 7-3. Wrap the memory process
    async def memory_worker_wrapper(job):
        """Worker that processes memory save tasks"""
        from app.cc_agents.memory_manager import call_memory_manager

        memory_query = job.get("memory_query")

        if not memory_query:
            logging.warning(f"[MEMORY_WRAPPER] No memory query in job")
            return

        logging.info(f"[MEMORY_WRAPPER] Saving memory: {memory_query[:100]}...")
        await call_memory_manager(memory_query)
        logging.info(f"[MEMORY_WRAPPER] Memory saved successfully")

    # 7-4. Start the workers
    from app.queueing_extended import start_orchestrator_worker, start_memory_worker

    start_channel_workers(app, process_wrapper, workers_per_channel=8)
    start_orchestrator_worker(app, orchestrator_wrapper, num_workers=3)
    start_memory_worker(memory_worker_wrapper)

    # 8. Start the scheduler
    await reload_schedules_from_file()

    # 8-1. Add MS365 (Outlook) checker job
    if settings.OUTLOOK_CHECK_ENABLED and settings.MS365_ENABLED:
        from app.cc_checkers.ms365.outlook_checker import check_email_updates

        # Register with scheduler
        scheduler.add_job(
            check_email_updates,
            trigger="interval",
            seconds=settings.OUTLOOK_CHECK_INTERVAL * 60,  # Convert minutes to seconds
            id="outlook_checker",
            name="MS365 Outlook Checker",
        )
        logging.info(
            f"[SCHEDULER] MS365 Outlook checker registered (interval: {settings.OUTLOOK_CHECK_INTERVAL} minutes)"
        )

    # 8-3. Add Atlassian checkers (Confluence & Jira)
    if settings.ATLASSIAN_ENABLED:
        # Confluence checker
        if settings.CONFLUENCE_CHECK_ENABLED:
            from app.cc_checkers.atlassian.confluence_checker import check_confluence_updates

            logging.info("[CONFLUENCE_CHECKER] Initializing Confluence checker...")
            scheduler.add_job(
                check_confluence_updates,
                trigger="interval",
                seconds=settings.CONFLUENCE_CHECK_INTERVAL * 60,
                id="confluence_checker",
                name="Confluence Checker",
            )
            logging.info(
                f"[SCHEDULER] Confluence checker registered (interval: {settings.CONFLUENCE_CHECK_INTERVAL} minutes)"
            )

        # Jira checker
        if settings.JIRA_CHECK_ENABLED:
            from app.cc_checkers.atlassian.jira_checker import check_jira_updates

            logging.info("[JIRA_CHECKER] Initializing Jira checker...")
            scheduler.add_job(
                check_jira_updates,
                trigger="interval",
                seconds=settings.JIRA_CHECK_INTERVAL * 60,
                id="jira_checker",
                name="Jira Checker",
            )
            logging.info(
                f"[SCHEDULER] Jira checker registered (interval: {settings.JIRA_CHECK_INTERVAL} minutes)"
            )

    # 8-4. Add dynamic suggester job
    if settings.DYNAMIC_SUGGESTER_ENABLED:
        from app.cc_agents.proactive_dynamic_suggester import call_dynamic_suggester

        logging.info("[DYNAMIC_SUGGESTER] Initializing dynamic suggester...")

        # Register with scheduler
        scheduler.add_job(
            call_dynamic_suggester,
            trigger="interval",
            minutes=settings.DYNAMIC_SUGGESTER_INTERVAL,
            id="dynamic_suggester",
            name="Dynamic Suggester",
        )
        logging.info(
            f"[SCHEDULER] Dynamic suggester registered (interval: {settings.DYNAMIC_SUGGESTER_INTERVAL} minutes)"
        )

    scheduler.start()

    # 9. Start FastAPI Web Server (voice interface)
    web_server = None
    web_server_task = None

    if settings.WEB_INTERFACE_ENABLED:
        logging.info("[WEB_SERVER] Starting FastAPI web server on port 8000...")
        import uvicorn
        from pathlib import Path
        from app.cc_web_interface.server import web_app

        # SSL certificate path
        cert_dir = Path(__file__).parent / "config" / "certs"
        ssl_keyfile = str(cert_dir / "key.pem")
        ssl_certfile = str(cert_dir / "cert.pem")

        # Run FastAPI in separate task (HTTPS)
        config = uvicorn.Config(
            web_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )
        web_server = uvicorn.Server(config)
        web_server_task = asyncio.create_task(web_server.serve())
        logging.info("[WEB_SERVER] Web server started at https://localhost:8000")
        logging.info("[WEB_SERVER] Access from other devices: https://YOUR_IP:8000")
    else:
        logging.info("[WEB_SERVER] Web interface disabled")

    # 9-1. X authentication check and handling
    if settings.X_ENABLED:
        from app.cc_utils.x_helper import load_token
        from app.cc_tools.x import initialize_x_client
        import webbrowser

        # Initialize OAuth 1.0a client (for tweet posting, media upload, timeline)
        if all(
            [
                settings.X_API_KEY,
                settings.X_API_SECRET,
                settings.X_ACCESS_TOKEN,
                settings.X_ACCESS_TOKEN_SECRET,
            ]
        ):
            try:
                client = initialize_x_client()
                me = client.get_me()
                username = me.data.username
                name = me.data.name
                logging.info(
                    f"[X_CLIENT] ✅ OAuth 1.0a authenticated as @{username} ({name})"
                )
            except Exception as e:
                logging.error(f"[X_CLIENT] ❌ OAuth 1.0a authentication failed: {e}")
        else:
            logging.warning("[X_CLIENT] OAuth 1.0a credentials not configured")

        # OAuth 2.0 token check (for tweet viewing, search)
        token = load_token()
        if not token:
            logging.warning("[X_OAUTH] No OAuth 2.0 token found")
            print("\n" + "=" * 70)
            print("🔐 X (Twitter) OAuth 2.0 Authentication Required")
            print("=" * 70)
            print("\nTo enable follow/unfollow/following features:")
            print("  https://localhost:8000/bot/auth/x/start")
            print("\nOpening browser for authentication...")
            print("=" * 70 + "\n")

            # Wait for web server to start (1 second)
            await asyncio.sleep(1)

            # Open browser
            webbrowser.open("https://localhost:8000/bot/auth/x/start")

            # Wait for token generation (max 3 minutes)
            timeout = 180
            start_time = asyncio.get_event_loop().time()

            while True:
                token = load_token()
                if token:
                    logging.info("[X_OAUTH] ✅ OAuth 2.0 authentication completed!")
                    break

                if asyncio.get_event_loop().time() - start_time > timeout:
                    logging.error("[X_OAUTH] ❌ Authentication timeout (3 minutes)")
                    logging.warning(
                        "[X_OAUTH] Follow/unfollow features will not work until authenticated"
                    )
                    break

                await asyncio.sleep(2)
        else:
            logging.info("[X_OAUTH] ✅ OAuth 2.0 token found, X features ready")

    # 10. Start Slack Socket Mode handler
    logging.info("Starting Socket Mode handler...")
    handler = AsyncSocketModeHandler(app, settings.SLACK_APP_TOKEN)

    try:
        await handler.start_async()
    except KeyboardInterrupt:
        logging.info("\n[SHUTDOWN] Graceful shutdown initiated...")

        # 1. Shutdown web server
        if web_server and web_server_task:
            logging.info("[SHUTDOWN] Stopping web server...")
            web_server.should_exit = True
            web_server_task.cancel()
            try:
                await web_server_task
            except asyncio.CancelledError:
                pass

        # 2. Shutdown scheduler
        logging.info("[SHUTDOWN] Stopping scheduler...")
        scheduler.shutdown()

        # 3. Shutdown handler
        logging.info("[SHUTDOWN] Stopping Slack handler...")
        await handler.close_async()

        logging.info("[SHUTDOWN] ✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
