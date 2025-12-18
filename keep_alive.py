# keep_alive.py
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder

app = Flask(__name__)

from telegram_chatbot import bot_app  # import the bot instance

TOKEN = os.getenv("TELEGRAM_TOKEN")

@app.route("/", methods=["GET"])
def index():
    return "Bot is running ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Telegram will POST updates here"""
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put(update)  # send update to the bot
    return "ok"
