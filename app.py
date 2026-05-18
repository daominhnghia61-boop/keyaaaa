import json
import os
import datetime
import secrets
import logging
import asyncio

from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
BOT_TOKEN = "8631913457:AAGVoswxWXSIVUve7XqV2FnZtizo0jEOJwM"
ADMIN_ID = 8522186660
KEYS_FILE = "keys.json"

WEBHOOK_URL = "https://web-production-c4ed6.up.railway.app"
SECRET_PATH = "botwebhook"

# ---------------- LOG ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- APP ----------------
app = Flask(__name__)

# ---------------- KEY STORAGE ----------------
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# ---------------- TELEGRAM ----------------
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot đang chạy ngon rồi!")

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
    expire = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat()

    keys = load_keys()
    keys[key] = {"expire": expire}
    save_keys(keys)

    await update.message.reply_text(
        f"✅ Key: `{key}`\n📅 Hết hạn: {expire}",
        parse_mode="Markdown"
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("genkey", gen_key))

# ---------------- INIT BOT (QUAN TRỌNG) ----------------
async def init_bot():
    await application.initialize()
    await application.start()

asyncio.run(init_bot())

# ---------------- FLASK ROUTES ----------------

@app.route("/")
def home():
    return "SERVER OK"

@app.route("/check")
def check_key():
    key = request.args.get("key", "").strip().upper()

    if not key:
        return "NO_KEY"

    keys = load_keys()

    if key not in keys:
        return "INVALID"

    expire = datetime.datetime.fromisoformat(keys[key]["expire"])

    if datetime.datetime.utcnow() > expire:
        return "EXPIRED"

    return "VALID"

# ---------------- WEBHOOK ----------------
@app.route(f"/webhook/{SECRET_PATH}", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)

    asyncio.run(
        application.process_update(
            Update.de_json(data, application.bot)
        )
    )

    return "OK"

# ---------------- SET WEBHOOK ----------------
@app.route("/setwebhook")
def set_webhook():
    async def setup():
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook/{SECRET_PATH}"
        )
        return "OK"

    return asyncio.run(setup())
