import json
import os
import datetime
import secrets
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== CẤU HÌNH ==========
BOT_TOKEN = "8631913457:AAGVoswxWXSIVUve7XqV2FnZtizo0jEOJwM"
ADMIN_ID = 8522186660
KEYS_FILE = "keys.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== KEY STORAGE ==========
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# ========== TELEGRAM HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot key auth đang chạy!\nAdmin dùng /genkey <số_ngày>")

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
    await update.message.reply_text(
        f"✅ Key: `{key}`\n📅 Hết hạn: {expire}",
        parse_mode="Markdown"
    )

# ========== FLASK ROUTES ==========
@app.route("/")
def home():
    return "Bot is running!"

@app.route("/check", methods=['GET'])
def check_key():
    key = request.args.get("key", "").strip().upper()
    keys = load_keys()
    if key not in keys:
        return "INVALID"
    if datetime.datetime.now() < datetime.datetime.fromisoformat(keys[key]["expire"]):
        return "VALID"
    return "EXPIRED"

# ========== WEBHOOK ==========
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("genkey", gen_key))

@app.route("/webhook", methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        application.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR", 500

# ========== MAIN ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Set webhook
    import asyncio
    async def set_webhook():
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(url=f"https://web-production-c4ed6.up.railway.app/webhook")
        logger.info("✅ Webhook set successfully")
    
    asyncio.run(set_webhook())
    
    # Chạy Flask
    app.run(host="0.0.0.0", port=port)
