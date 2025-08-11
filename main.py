#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import asyncio
import os
import requests
from flask import Flask, request, abort
from pyrogram import errors, Client
from utils import LOGGER
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    WEBHOOK
)
from misc import handle_callback_query
from modules import setup_modules_handlers
from sudoers import setup_sudoers_handlers
from core import setup_start_handler
from app import app
from user import user

# Flask app initialization
web_app = Flask(__name__)

# CONNECT ALL MODULES WITH BOT AND USER CLIENT
setup_modules_handlers(app)
setup_sudoers_handlers(app)
setup_start_handler(app)

@app.on_callback_query()
async def handle_callback(client, callback_query):
    await handle_callback_query(client, callback_query)

# Webhook function to handle incoming requests
@web_app.route("/", methods=["POST"])
async def telegram_webhook():
    if request.json:
        # Pass the update to Pyrogram
        try:
            update = request.json
            await app.process_update(update)
        except errors.RPCError as e:
            LOGGER.error(f"Error processing update: {e}")
            abort(500)
    return "OK", 200

# Set Webhook URL to Telegram
def set_webhook():
    webhook_url = f"https://your-app-name.railway.app/" # Change this to your Railway app domain
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, data={'url': webhook_url})
        if response.status_code == 200:
            LOGGER.info(f"Webhook set to {webhook_url}")
        else:
            LOGGER.error(f"Failed to set webhook. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        LOGGER.error(f"Error setting webhook: {e}")

if __name__ == "__main__":
    if WEBHOOK:
        # Webhook mode for Railway deployment
        LOGGER.info("Starting Bot in Webhook Mode")
        app.start()
        set_webhook()
        # Run Flask app with the port from environment variable
        port = int(os.environ.get("PORT", 8000))
        web_app.run(host="0.0.0.0", port=port)
        app.stop()
    else:
        # Long Polling mode for local or VPS deployment
        LOGGER.info("Starting Bot in Long Polling Mode")
        user.start()
        app.run()
