import os
import json
import re
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# -------------------------------
# Flask App
# -------------------------------
app = Flask(__name__)

# -------------------------------
# Load .env
# -------------------------------
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CIRCLE_DATA_ENV = os.getenv("CIRCLE_DATA")

if not TOKEN:
    raise ValueError("⚠ TELEGRAM_TOKEN not found in .env")

if not CIRCLE_DATA_ENV:
    raise ValueError("⚠ CIRCLE_DATA not found in .env")

# Load circle data
try:
    DATA = json.loads(CIRCLE_DATA_ENV)
except json.JSONDecodeError as e:
    raise ValueError(f"⚠ Failed to parse CIRCLE_DATA JSON: {e}")

# -------------------------------
# Circle names and aliases
# -------------------------------
CIRCLE_FULL_NAMES = {
    "DEL": "Delhi",
    "UPW": "Uttar Pradesh West",
    "PUN": "Punjab",
    "HP": "Himachal Pradesh",
    "UPE": "Uttar Pradesh East",
    "J&K": "Jammu & Kashmir",
    "HAR": "Haryana",
    "KOL": "Kolkata",
    "WB": "West Bengal",
    "NESA": "North East & Sikkim & Assam",
    "ASSAM": "Assam",
    "ORISSA": "Orissa",
    "BIHAR": "Bihar",
    "KK": "Karnataka & Kerala",
    "TN": "Tamil Nadu",
    "AP": "Andhra Pradesh",
    "KER": "Kerala",
    "RAJ": "Rajasthan",
    "MAH": "Maharashtra",
    "MUM": "Mumbai",
    "MP": "Madhya Pradesh",
    "GUJ": "Gujarat"
}

CIRCLE_ALIASES = {
    "J&K": ["jk","j&k","j and k","jammu kashmir","jammu and kashmir","jammu & kashmir"],
    "AP": ["andhra","andhra pradesh","ap"],
    "UPW": ["up west","uttar pradesh west"],
    "UPE": ["up east","uttar pradesh east"],
    "HAR": ["haryana","hr"],
    "MAH": ["maharashtra","mh"],
    "GUJ": ["gujarat","gj"],
}

# -------------------------------
# Utility Functions
# -------------------------------
def normalize(text: str) -> str:
    """Lowercase, remove special chars except space and &"""
    return re.sub(r"[^a-z0-9 &]", "", text.lower())

def extract_hub_number(text: str):
    match = re.search(r"hub\s*(\d+)", text.lower())
    return match.group(1) if match else None

def find_circle(user_text: str):
    text = normalize(user_text)
    for circle, aliases in CIRCLE_ALIASES.items():
        for alias in aliases:
            if alias in text:
                return circle
    for circle, full_name in CIRCLE_FULL_NAMES.items():
        if normalize(full_name) in text:
            return circle
    for circle in DATA.keys():
        if circle.lower() in text.split():
            return circle
    return None

def get_response(user_input: str) -> str:
    text = normalize(user_input)
    circle = find_circle(text)
    hub_no = extract_hub_number(text)

    if hub_no:
        circles = [c for c, info in DATA.items() if info["hub"].lower().endswith(hub_no)]
        if circles:
            return f"Hub {hub_no} me circles hain: " + ", ".join(circles)
        return f"Hub {hub_no} me koi circle nahi mila"

    if not circle:
        return "❓ Circle ka naam clear nahi hai (Delhi / Assam / UPW etc)"

    info = DATA[circle]
    if "in" in text:
        return f"{circle} ka IN : {info['in']}"
    if "hub" in text:
        return f"{circle} ka Hub : {info['hub']} ({info['hub_name']})"
    if "group" in text:
        return f"{circle} ka Group ID : {info['group_id']}"
    if "circle code" in text or "code" in text:
        return f"{circle} ka Circle Code : {info['circle_code']}"
    if "dth" in text:
        return f"{circle} ka DTH Circle Code : {info.get('dth_circle_code','N/A')}"
    return f"❓ Question thoda clear poochiye (hub / in / code / group / dth). {circle} - {CIRCLE_FULL_NAMES.get(circle)}"

# -------------------------------
# Telegram Handlers
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Circle Chatbot is active.\nAsk me about IN, Hub, Group, Circle Code, or DTH."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = get_response(user_text)
    await update.message.reply_text(response)

# -------------------------------
# Telegram Bot Setup (Webhook)
# -------------------------------
bot_app = ApplicationBuilder().token(TOKEN).build()
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot = bot_app.bot

# Flask route for Telegram webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    bot_app.update_queue.put(update)
    return "OK"

# Route to test server
@app.route("/")
def index():
    return "Circle Chatbot is running!"

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    # Start Telegram bot in background
    bot_app.start()
    bot_app.updater.start_polling()  # Optional, for local testing
    # Start Flask server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
