import json
import os
import datetime
import secrets
import logging

from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
BOT_TOKEN = ("8631913457:AAGVoswxWXSIVUve7XqV2FnZtizo0jEOJwM")  # set trên Railway
ADMIN_ID = 8522186660
KEYS_FILE = "keys.json"

# 🔥 DOMAIN CỐ ĐỊNH CỦA BẠN
WEBHOOK_URL = "https://web-production-c4ed6.up.railway.app"

# 🔒 path bí mật (không dùng token trực tiếp)
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
    expire = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()

    keys = load_keys()
    keys[key] = {"expire": expire}
    save_keys(keys)

    await update.message.reply_text(
        f"✅ Key: `{key}`\n📅 Hết hạn: {expire}",
        parse_mode="Markdown"
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("genkey", gen_key))

# ---------------- FLASK ROUTES ----------------

@app.route("/")
def home():
    return "OK"

@app.route("/check")
def check_key():
    key = request.args.get("key", "").strip().upper()
    keys = load_keys()

    if key not in keys:
        return "INVALID"

    if datetime.datetime.now() < datetime.datetime.fromisoformat(keys[key]["expire"]):
        return "VALID"

    return "EXPIRED"

# 👉 webhook nhận update từ Telegram
@app.route(f"/webhook/{SECRET_PATH}", methods=["POST"])
async def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "OK"

# ---------------- START ----------------

if __name__ == "__main__":
    import asyncio

    async def setup():
        logger.info("Setting webhook...")
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook/{SECRET_PATH}"
        )
        logger.info("Webhook set DONE")

    asyncio.run(setup())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
