import json
import os
import datetime
import secrets
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8798908847:AAF5jX_UKtiE4BtUWAVEsJ7_so0BWqbf8Y4"
ADMIN_ID = 8522186660
KEYS_FILE = "keys.json"

app = Flask(__name__)

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

if __name__ == "__main__":
    # Chạy Flask trong thread phụ
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Chạy bot ở main thread
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genkey", gen_key))
    application.run_polling()
