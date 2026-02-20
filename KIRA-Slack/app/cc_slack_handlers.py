import logging
import random
import re
from app.queueing_extended import debounced_enqueue_message, enqueue_orchestrator_job
from app.cc_utils.language_helper import detect_language
from app.cc_utils.slack_helper import get_slack_context_data
from app.cc_agents.bot_call_detector import call_bot_call_detector
from app.cc_agents.bot_thread_context_detector import call_bot_thread_context_detector
from app.cc_agents.answer_aggregator import call_answer_aggregator
from app.cc_agents.memory_retriever import call_memory_retriever
from app.cc_agents.simple_chat import call_simple_chat
from app.cc_agents.proactive_suggester import call_proactive_suggester
from app.cc_agents.proactive_confirm import call_proactive_confirm
from app.config.settings import get_settings
from slack_sdk import WebClient

# =============================================
# Global Bot User ID
# =============================================
_bot_user_id = None

def set_bot_user_id(user_id: str):
    """Set bot user ID"""
    global _bot_user_id
    _bot_user_id = user_id

def get_bot_user_id() -> str:
    """Return bot user ID"""
    return _bot_user_id

# =============================================
# Utils
# =============================================

def is_authorized_user(user_name: str) -> bool:
    """
    Check if the user is an authorized user.

    Args:
        user_name: Slack user name (display_name or real_name)

    Returns:
        bool: True if authorized user, False otherwise
    """
    settings = get_settings()
    authorized_users = []

    if settings.BOT_AUTHORIZED_USERS_EN:
        authorized_users.extend(settings.BOT_AUTHORIZED_USERS_EN.split(", "))
    if settings.BOT_AUTHORIZED_USERS_KR:
        authorized_users.extend(settings.BOT_AUTHORIZED_USERS_KR.split(", "))

    # Allow all users if authorized list is empty
    if not authorized_users:
        return True

    # Check if authorized name is contained in user name
    return any(auth_user in user_name for auth_user in authorized_users)


async def get_user_name(user_id: str, client: WebClient) -> str:
    """
    Get user name from Slack user_id.

    Args:
        user_id: Slack user ID
        client: Slack WebClient

    Returns:
        str: display_name or real_name (returns user_id on failure)
    """
    try:
        response = await client.users_info(user=user_id)
        if response["ok"]:
            user = response["user"]
            profile = user.get("profile", {})
            # Prefer display_name, use real_name if not available
            return profile.get("display_name") or user.get("real_name", user_id)
    except Exception as e:
        logging.warning(f"Failed to fetch user info for {user_id}: {e}")

    return user_id


async def convert_mentions_to_readable(text: str, client: WebClient) -> str:
    """
    Convert Slack mention format <@U12345> to human-readable format
    Example: <@U12345> -> Seungjin Kwon(@U12345)
    """
    # Find all mentions
    pattern = r'<@([A-Z0-9]+)>'
    matches = re.finditer(pattern, text)

    # Create user_id -> real_name mapping
    user_map = {}
    for match in matches:
        user_id = match.group(1)
        if user_id not in user_map:
            try:
                # Fetch user info via Slack API
                response = await client.users_info(user=user_id)
                if response["ok"]:
                    user = response["user"]
                    profile = user.get("profile", {})
                    # Prefer display_name, use real_name if not available
                    display_name = profile.get("display_name") or user.get("real_name", f"User {user_id}")
                    user_map[user_id] = f"{display_name}(@{user_id})"
                else:
                    user_map[user_id] = f"<@{user_id}>"
            except Exception as e:
                logging.warning(f"Failed to fetch user info for {user_id}: {e}")
                user_map[user_id] = f"<@{user_id}>"

    # Transform text
    def replace_mention(match):
        user_id = match.group(1)
        return user_map.get(user_id, match.group(0))

    return re.sub(pattern, replace_mention, text)

# =============================================
# Message Processing
# =============================================

async def _process_message_logic(message, client):
    channel_id = message.get("channel")
    user_id = message.get("user")
    user_text = message.get("text", "")
    message_ts = message.get("ts")
    thread_ts = message.get("thread_ts")
    skip_ack_messages = message.get("skip_ack_messages", False)  # Skip approval/busy messages for scheduled tasks

    # Ignore specific channels
    IGNORED_CHANNELS = ["C01DPSN7NVB", "C0GCR4908"]
    if channel_id in IGNORED_CHANNELS:
        return

    # Message received log
    logging.info(f"[MESSAGE_RECEIVED] channel={channel_id}, user={user_id}, text='{user_text[:50]}...', ts={message_ts}")

    # Get user name
    user_name = await get_user_name(user_id, client)

    user_text = await convert_mentions_to_readable(user_text, client)

    # Collect channel info from Slack API
    slack_data = get_slack_context_data(channel_id, message_limit=10)

    # Add current message info
    message_data = {
        "user_id": user_id,
        "user_name": user_name,
        "user_text": user_text,
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "message_ts": message_ts,
    }

    # Add file info if files are attached
    if message.get("files"):
        message_data["files"] = message.get("files")

    # Proactive Confirm check: Check if user responded to pending confirm
    logging.info(f"[PROACTIVE_CONFIRM] Checking for pending confirms (user={user_id}, channel={channel_id}, thread_ts={thread_ts})")
    approved, original_message = await call_proactive_confirm(user_text, channel_id, user_id, thread_ts)

    if approved and original_message:
        logging.info(f"[PROACTIVE_CONFIRM] User approved! Processing original message: '{original_message['user_text'][:50]}...'")

        # Check channel type (DM vs group channel)
        channel_type = slack_data.get("channel", {}).get("channel_type", "")

        # DM: respond in main, Group channel: respond in thread
        if channel_type == "dm":
            approval_thread_ts = None  # DM: respond in main
            operator_thread_ts = None
            logging.info(f"[PROACTIVE_CONFIRM] DM detected, responding in main channel")
        else:
            approval_thread_ts = thread_ts or message_ts  # Group channel: respond in thread
            operator_thread_ts = thread_ts
            logging.info(f"[PROACTIVE_CONFIRM] Group channel detected, responding in thread")

        # Approval response message samples (selected by language)
        if not skip_ack_messages:
            original_text = original_message.get("user_text", "")
            lang = detect_language(original_text)

            if lang == "Korean":
                approval_messages = [
                    "알겠습니다! 처리해드릴게요.",
                    "넵, 바로 확인해드릴게요.",
                    "네, 진행하겠습니다.",
                    "알겠어요. 처리하겠습니다.",
                    "확인했습니다. 바로 진행할게요."
                ]
            else:
                approval_messages = [
                    "Got it! I'll take care of it.",
                    "Sure, I'll check on that right away.",
                    "Okay, I'll proceed.",
                    "Understood. I'll handle it.",
                    "Confirmed. I'll get started right away."
                ]

            await client.chat_postMessage(
                channel=channel_id,
                text=random.choice(approval_messages),
                thread_ts=approval_thread_ts
            )

        # Update original_message to current context (so operator responds in correct thread)
        original_message["message_ts"] = message_ts
        original_message["thread_ts"] = operator_thread_ts
        original_message["channel_id"] = channel_id  # Also update channel

        original_user_text = original_message["user_text"]
        original_user_id = original_message["user_id"]
        original_user_name = original_message["user_name"]

        memory_query = f"""Please gather and provide the memory needed to fulfill user {original_user_name}({original_user_id})'s request '{original_user_text}' in channel {channel_id}.
Be sure to include **guidelines** and information (channel_id, user_id, user_name) about this channel and requesting user."""
        
        retrieved_memory = await call_memory_retriever(
            memory_query,
            slack_data,
            original_message
        )
        logging.info(f"[PROACTIVE_CONFIRM] Memory retrieved for original message: {retrieved_memory[:100] if retrieved_memory else 'None'}...")

        # orchestrator job enqueue
        orchestrator_job = {
            "query": original_user_text,
            "slack_data": slack_data,
            "message_data": original_message,
            "retrieved_memory": retrieved_memory
        }
        await enqueue_orchestrator_job(orchestrator_job)
        logging.info(f"[PROACTIVE_CONFIRM] Original message enqueued to orchestrator successfully")
        return

    # Bot call check logic for group channels/group DMs
    channel_type = slack_data.get("channel", {}).get("channel_type", "")
    if channel_type in ["public_channel", "private_channel", "group_dm"]:
        logging.info(f"[BOT_CALL_CHECK] Checking if bot is called in group context (channel={channel_id}, type={channel_type})")
        is_bot_called = await call_bot_call_detector(user_text)
        logging.info(f"[BOT_CALL_RESULT] is_bot_called={is_bot_called}, user_text='{user_text[:50]}...'")

        # Check if bot should respond in thread even without explicit call
        if not is_bot_called and thread_ts:
            logging.info(f"[THREAD_CONTEXT_CHECK] Checking if bot is participating in thread (thread_ts={thread_ts})")
            is_bot_in_thread = await call_bot_thread_context_detector(thread_ts, channel_id, user_text, client)
            logging.info(f"[THREAD_CONTEXT_RESULT] is_bot_in_thread={is_bot_in_thread}")
            if is_bot_in_thread:
                is_bot_called = True
                logging.info(f"[THREAD_CONTEXT] Bot participating in thread, treating as bot call")

        if not is_bot_called:
            # Proactive system: Check if similar work was done before
            logging.info(f"[PROACTIVE] Checking if bot can proactively suggest help (user={user_id}, channel={channel_id})")

            # 1. Memory search (for proactive)
            proactive_memory_query = f"""The user made a request '{user_text}'. Please gather memory to check if I've done similar work before.
Be sure to include **guidelines** and information (channel_id, user_id, user_name) about this channel and requesting user."""
            
            retrieved_memory = await call_memory_retriever(
                proactive_memory_query,
                slack_data,
                message_data
            )
            logging.info(f"[PROACTIVE] Memory retrieved: {retrieved_memory[:100] if retrieved_memory else 'None'}...")

            # 2. Call proactive_suggester
            suggested = await call_proactive_suggester(
                user_text=user_text,
                retrieved_memory=retrieved_memory,
                slack_data=slack_data,
                message_data=message_data
            )

            if suggested:
                logging.info(f"[PROACTIVE] Suggestion sent to user, stopping message processing")
                return

            # Exit if no memory or no suggestion made
            logging.info(f"[BOT_CALL_SKIPPED] Bot not called in group channel, skipping message processing")
            return
        logging.info(f"[BOT_CALLED] Bot was called, proceeding with message processing")

    # Response aggregation logic
    logging.info(f"[RESPONSE_PROCESSING] Calling answer_aggregator (user={user_id}, channel={channel_id})")
    is_answer_completed = await call_answer_aggregator(user_text, message_data)
    logging.info(f"[ANSWER_AGGREGATOR_RESULT] is_answer_completed={is_answer_completed}")
    if is_answer_completed:
        logging.info(f"[RESPONSE_COMPLETED] Answer aggregator processed the message, skipping simple_chat and orchestrator (user={user_id})")
        return

    # Authorization check: Only process authorized users (check for new requests only)
    if not is_authorized_user(user_name):
        logging.info(f"[UNAUTHORIZED] User '{user_name}'({user_id}) is not authorized, skipping message")

        # Send busy message only if skip_ack_messages is False
        if not skip_ack_messages:
            # Calculate thread_ts based on channel_type
            channel_type = slack_data.get("channel", {}).get("channel_type", "")
            if channel_type in ["public_channel", "private_channel", "group_dm"]:
                # Group channel: always respond in thread
                final_thread_ts = thread_ts or message_ts
            elif channel_type in ["dm"]:
                # DM/Group DM: respond in thread if thread_ts exists, otherwise normal message
                final_thread_ts = thread_ts
            else:
                final_thread_ts = None

            # 바쁨 응답 메시지 샘플 (언어에 따라 선택)
            lang = detect_language(user_text)

            if lang == "Korean":
                busy_messages = [
                    "지금 급한 업무가 있어서 조금 있다가 답변드릴게요.",
                    "팀 업무로 바빠서 답변이 어렵습니다. 죄송합니다.",
                    "급한 일 처리 중이라 시간이 좀 걸릴 것 같아요.",
                    "지금은 다른 작업 중이라 나중에 확인하고 답변드릴게요.",
                    "업무 중이라 바로 답변이 어려울 것 같습니다. 조금만 기다려주세요."
                ]
            else:
                busy_messages = [
                    "I'm busy with urgent work right now. I'll get back to you soon.",
                    "I'm tied up with team work at the moment. Sorry about that.",
                    "I'm handling something urgent, so it might take a while.",
                    "I'm working on something else right now. I'll check and respond later.",
                    "I'm in the middle of work, so I can't respond immediately. Please wait a moment."
                ]

            # Send message
            post_params = {
                "channel": channel_id,
                "text": random.choice(busy_messages)
            }

            if final_thread_ts:
                post_params["thread_ts"] = final_thread_ts

            await client.chat_postMessage(**post_params)
        return

    # Memory retrieval (shared by simple_chat and orchestrator)
    logging.info(f"[MEMORY_RETRIEVER] Retrieving memory (user={user_id}, channel={channel_id})")
    memory_query = f"""Please gather and provide the memory needed to fulfill user {user_name}({user_id})'s request '{user_text}' in channel {channel_id}.
Be sure to include **guidelines** and information (channel_id, user_id, user_name) about this channel and requesting user."""
    
    retrieved_memory = await call_memory_retriever(
        memory_query,
        slack_data,
        message_data
    )
    logging.info(f"[MEMORY_RETRIEVER] Memory retrieved: {retrieved_memory[:100] if retrieved_memory else 'None'}...")

    logging.info(f"[SIMPLE_CHAT] Calling simple_chat agent (user={user_id}, channel={channel_id})")
    is_simple_completed = await call_simple_chat(user_text, slack_data, message_data, retrieved_memory)
    logging.info(f"[SIMPLE_CHAT_RESULT] is_simple_completed={is_simple_completed}")

    # Skip orchestrator if simple_chat handled the message
    if is_simple_completed:
        logging.info(f"[RESPONSE_COMPLETED] Simple chat processed the message, skipping orchestrator (user={user_id})")
        return

    # Complex task → forward to orchestrator
    logging.info(f"[ORCHESTRATOR_ENQUEUE] Enqueuing orchestrator job (user={user_id}, channel={channel_id})")
    orchestrator_job = {
        "query": user_text,
        "slack_data": slack_data,
        "message_data": message_data,
        "retrieved_memory": retrieved_memory  # Pass already retrieved memory
    }
    await enqueue_orchestrator_job(orchestrator_job)
    logging.info(f"[ORCHESTRATOR_ENQUEUED] Orchestrator job enqueued successfully (user={user_id})")
    
# =============================================
# Slack Event Handler Registration
# =============================================

def register_handlers(app):
    """Register all Slack event handlers."""

    async def is_dm(body):
        """1:1 DM or group DM (mpim)"""
        channel_type = body.get("event", {}).get("channel_type")
        return channel_type in ["im", "mpim"]

    async def is_channel(body):
        """Public/private channels only"""
        channel_type = body.get("event", {}).get("channel_type")
        return channel_type in ["channel", "group"]

    async def is_bot_in_channel(body, client):
        """Check if bot is a member of the channel (for User Token filter)"""
        channel_id = body.get("event", {}).get("channel")
        if not channel_id:
            return False

        try:
            # Check if bot is a member by fetching channel info
            result = await client.conversations_info(channel=channel_id)
            return result.get("channel", {}).get("is_member", False)
        except Exception as e:
            # Return False if channel info fetch fails (e.g., no permission)
            logging.debug(f"Channel membership check failed for {channel_id}: {e}")
            return False

    async def has_files(body):
        """Check if message has file attachments"""
        event = body.get("event", {})
        return event.get("files") or event.get("subtype") == "file_share"

    async def has_links(body):
        """Check if message contains links"""
        event = body.get("event", {})
        text = event.get("text", "")
        return "http://" in text or "https://" in text


    @app.event("message", matchers=[is_dm])
    async def handle_dm_message(event, body, client):
        """Handle DM messages (1:1 DM + group DM, always processed, no channel membership check needed)"""
        # Exclude bot messages
        if event.get("bot_id") is not None:
            return

        # Exclude bot's own messages (when using user token)
        bot_user_id = get_bot_user_id()
        if bot_user_id and event.get("user") == bot_user_id:
            return

        # Exclude Slackbot system notifications
        if event.get("user") == "USLACKBOT":
            return

        # Check file message (before subtype check!)
        if await has_files(body):
            await debounced_enqueue_message(event, delay_seconds=5.0)
            return

        # Check link message
        if await has_links(body):
            await debounced_enqueue_message(event, delay_seconds=5.0)
            return

        # Ignore messages with subtype (edit, delete, etc.)
        subtype = event.get("subtype")
        if subtype is not None:
            return

        # Process pure text messages (both normal and thread messages)
        await debounced_enqueue_message(event, delay_seconds=5.0)
        return


    @app.event("message", matchers=[is_channel, is_bot_in_channel])
    async def handle_channel_message(event, body, client):
        """Handle channel messages (public/private channels, only where bot is a member)"""
        # Exclude bot messages
        if event.get("bot_id") is not None:
            return

        # Exclude bot's own messages (when using user token)
        bot_user_id = get_bot_user_id()
        if bot_user_id and event.get("user") == bot_user_id:
            return

        # Exclude Slackbot system notifications
        if event.get("user") == "USLACKBOT":
            return

        # Check file message (before subtype check!)
        if await has_files(body):
            await debounced_enqueue_message(event, delay_seconds=5.0)
            return

        # Check link message
        if await has_links(body):
            await debounced_enqueue_message(event, delay_seconds=5.0)
            return

        # Ignore messages with subtype (edit, delete, etc.)
        subtype = event.get("subtype")
        if subtype is not None:
            return

        # Process pure text messages (both normal and thread messages)
        await debounced_enqueue_message(event, delay_seconds=5.0)
        return


    # === Explicitly excluded events ===
    # (Not subscribed in Slack app)

    # reaction_added - emoji added (not subscribed)
    # reaction_removed - emoji removed (not subscribed)

    # === Ignored events (log only) ===

    # app_mention - bot mention notification (already handled via message event)
    @app.event("app_mention")
    async def ignore_app_mention(body, logger):
        logger.debug("app_mention event ignored (already handled via message event)")

    # file_shared - file share notification (already handled via message event)
    @app.event("file_shared")
    async def ignore_file_shared(body, logger):
        logger.debug("file_shared event ignored (already handled via message event)")

    # link_shared - link share notification (already handled via message event)
    @app.event("link_shared")
    async def ignore_link_shared(body, logger):
        logger.debug("link_shared event ignored (already handled via message event)")

    # member_joined_channel - member joined channel
    @app.event("member_joined_channel")
    async def ignore_member_joined(body, logger):
        logger.debug("member_joined_channel event ignored")

    # member_left_channel - member left channel
    @app.event("member_left_channel")
    async def ignore_member_left(body, logger):
        logger.debug("member_left_channel event ignored")

    # channel_left - bot left/removed from channel
    @app.event("channel_left")
    async def ignore_channel_left(body, logger):
        logger.debug("channel_left event ignored")

    # group_left - bot left group
    @app.event("group_left")
    async def ignore_group_left(body, logger):
        logger.debug("group_left event ignored")

    # All other message subtypes (edit, delete, join/leave, etc.)
    @app.event("message")
    async def handle_other_message_subtypes(body, logger):
        event = body.get("event", {})
        subtype = event.get("subtype")
        if subtype is not None:
            logger.debug(
                f"Message subtype ignored: {subtype} in {event.get('channel')}"
            )
