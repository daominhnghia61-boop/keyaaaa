import json
import logging
import os
import datetime
import secrets
import threading
import __main__ as _main_module
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8840678335:AAFoipq3y6csDEFxx6qXEMw0_3GvUwWWWYQ"
ADMIN_ID = 8522186660
KEYS_FILE = "keys.json"

app = Flask(__name__)
logger.info("Flask application object created")

def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

async def gen_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bạn không phải admin!")
        return
    if not context.args:
        await update.message.reply_text("⚠️ /genkey <số_ngày>")
        return
    try:
        days = int(context.args[0])
    except:
        await update.message.reply_text("⚠️ Số ngày không hợp lệ!")
        return

    key = secrets.token_hex(8).upper()
    expire = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    keys = load_keys()
    keys[key] = {"expire": expire, "created_by": update.effective_user.id}
    save_keys(keys)
    await update.message.reply_text(f"✅ Key: `{key}`\n📅 Hết hạn: {expire}", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot key auth đang chạy!\nAdmin dùng /genkey <số_ngày>")

@app.route('/check', methods=['GET'])
def check_key():
    key = request.args.get('key', '').strip().upper()
    keys = load_keys()
    if key not in keys:
        return "INVALID"
    if datetime.datetime.now() < datetime.datetime.fromisoformat(keys[key]["expire"]):
        return "VALID"
    return "EXPIRED"

def run_flask():
    """Run Flask dev server — used only when app.py is the main script."""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

def run_bot_main_thread():
    """Build and start Telegram bot polling on the calling (main) thread.

    run_polling() installs asyncio signal handlers which are only allowed on
    the main thread.  Calling this from any other thread raises RuntimeError.
    """
    logger.info("run_bot_main_thread() — building Telegram application...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("Telegram application built successfully")

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("genkey", gen_key))
        logger.info("Command handlers registered: /start, /genkey")

        logger.info("Starting bot polling on main thread — listening for updates")
        application.run_polling()
        logger.info("Bot polling stopped (run_polling returned)")
    except Exception as exc:
        logger.exception("run_bot_main_thread() raised an unhandled exception: %s", exc)

# ---------------------------------------------------------------------------
# When gunicorn imports app.py (via wsgi.py), start Flask in a background
# daemon thread so the WSGI server keeps running, then run the bot on the
# main thread where asyncio signal handlers are permitted.
#
# When app.py is run directly (`python app.py`), the same logic applies via
# the __main__ block below.
# ---------------------------------------------------------------------------
_running_as_main = getattr(_main_module, "__file__", None) and \
    os.path.abspath(_main_module.__file__) == os.path.abspath(__file__)

if not _running_as_main:
    # Imported by gunicorn / wsgi.py — start Flask in background, bot on main thread
    logger.info("Module imported (gunicorn context) — starting Flask daemon thread...")
    try:
        _flask_thread = threading.Thread(target=run_flask, daemon=True, name="flask-server")
        _flask_thread.start()
        logger.info("Flask daemon thread started (thread id: %s)", _flask_thread.ident)
    except Exception as _exc:
        logger.exception("Failed to start Flask daemon thread: %s", _exc)

    logger.info("Running bot polling on main thread (gunicorn worker)...")
    run_bot_main_thread()

if __name__ == "__main__":
    # Direct execution: Flask in background daemon thread, bot on main thread
    logger.info("Direct execution — starting Flask daemon thread...")
    flask_thread = threading.Thread(target=run_flask, daemon=True, name="flask-server")
    flask_thread.start()
    logger.info("Flask daemon thread started, running bot on main thread...")
    run_bot_main_thread()
