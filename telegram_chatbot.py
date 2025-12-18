import os
import json
import re
from dotenv import load_dotenv
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -------------------------------
# Flask keep-alive app
# -------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Circle Chatbot is live 🎉"

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CIRCLE_DATA_ENV = os.getenv("CIRCLE_DATA")

if not TOKEN or not CIRCLE_DATA_ENV:
    raise ValueError("⚠ TELEGRAM_TOKEN or CIRCLE_DATA not found in .env")

try:
    DATA = json.loads(CIRCLE_DATA_ENV)
except json.JSONDecodeError as e:
    raise ValueError(f"⚠ Failed to parse CIRCLE_DATA JSON: {e}")

# -------------------------------
# Circle info
# -------------------------------
CIRCLE_FULL_NAMES = {
    "DEL": "Delhi", "UPW": "Uttar Pradesh West", "PUN": "Punjab",
    "HP": "Himachal Pradesh", "UPE": "Uttar Pradesh East", "J&K": "Jammu & Kashmir",
    "HAR": "Haryana", "KOL": "Kolkata", "WB": "West Bengal", "NESA": "North East & Sikkim & Assam",
    "ASSAM": "Assam", "ORISSA": "Orissa", "BIHAR": "Bihar", "KK": "Karnataka & Kerala",
    "TN": "Tamil Nadu", "AP": "Andhra Pradesh", "KER": "Kerala", "RAJ": "Rajasthan",
    "MAH": "Maharashtra", "MUM": "Mumbai", "MP": "Madhya Pradesh", "GUJ": "Gujarat"
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
# Utility functions
# -------------------------------
def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 &]", "", text.lower())

def extract_hub_number(text: str):
    match = re.search(r"hub\s*(\d+)", text.lower())
    return match.group(1) if match else None

def find_circle(user_text: str):
    text = normalize(user_text)
    # Alias matching
    for circle, aliases in CIRCLE_ALIASES.items():
        for alias in aliases:
            if alias in text:
                return circle
    # Full name matching
    for circle, full_name in CIRCLE_FULL_NAMES.items():
        if normalize(full_name) in text:
            return circle
    # Exact code
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

    return f"❓ Question thoda clear poochiye (hub / in / code / group / dth). {circle}"

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
# Main
# -------------------------------
if __name__ == "__main__":
    import asyncio

    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot is running...")

    # -------------------------------
    # Run both Flask and Telegram
    # -------------------------------
    # Run Telegram bot (async)
    async def run_all():
        # Flask server in background
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000))))
        # Telegram bot polling
        await bot_app.run_polling()

    asyncio.run(run_all())
