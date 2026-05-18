import threading
from telegram.ext import Application, CommandHandler
from app import app, start, gen_key, BOT_TOKEN


def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genkey", gen_key))
    application.run_polling()


# Start Telegram bot polling in a background thread when gunicorn loads this module
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
