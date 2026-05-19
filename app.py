import json
import os
import datetime
import secrets
import logging
import threading

from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
BOT_TOKEN = "8631913457:AAGVoswxWXSIVUve7XqV2FnZtizo0jEOJwM"
ADMIN_ID = 8522186660
KEYS_FILE = "keys.json"

# 👉 LINK RAILWAY CỦA BẠN (THÊM VÀO ĐÂY)
RAILWAY_URL = "https://web-production-c4ed6.up.railway.app"

# ---------------- LOG ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- FLASK ----------------
app = Flask(__name__)

# ---------------- KEY SYSTEM ----------------
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# ---------------- BOT ----------------
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot chạy OK\n"
        f"🌐 Check key: {RAILWAY_URL}/check?key=YOUR_KEY"
    )

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Không có quyền!")
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
        f"✅ KEY: `{key}`\n"
        f"📅 Hết hạn: {expire}\n\n"
        f"🔗 Check: {RAILWAY_URL}/check?key={key}",
        parse_mode="Markdown"
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("genkey", genkey))

# ---------------- API CHECK ----------------
@app.route("/check")
def check_key():
    key = request.args.get("key", "").strip().upper()

    if not key:
        return "NO_KEY"

    keys = load_keys()

    if key not in keys:
        return "INVALID"

    try:
        expire = datetime.datetime.fromisoformat(keys[key]["expire"])
    except:
        return "INVALID_DATA"

    if datetime.datetime.utcnow() > expire:
        return "EXPIRED"

    return "VALID"

# ---------------- RUN ----------------
if __name__ == "__main__":
    def run_api():
        app.run(host="0.0.0.0", port=int("PORT", 8080)))

    def run_bot():
        application.run_polling()

    threading.Thread(target=run_api).start()
    run_bot()
