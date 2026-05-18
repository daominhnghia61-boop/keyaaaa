import logging
import threading
from app import app, start_bot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Start Telegram bot polling in a background thread when gunicorn loads this
# module.  Any exception raised inside start_bot() is already caught and
# logged there, but we also wrap the thread creation itself so a failure here
# is never silent.
# ---------------------------------------------------------------------------
logger.info("wsgi.py loaded — spawning bot background thread...")
try:
    bot_thread = threading.Thread(target=start_bot, daemon=True, name="telegram-bot")
    bot_thread.start()
    logger.info("Bot thread started (thread id: %s)", bot_thread.ident)
except Exception as exc:
    logger.exception("Failed to start bot thread: %s", exc)
