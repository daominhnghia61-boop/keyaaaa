import threading
from app import app, start_bot


# Start Telegram bot polling in a background thread when gunicorn loads this module
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()
