# main.py
from misc import handle_callback_query
from utils import LOGGER
from modules import setup_modules_handlers
from sudoers import setup_sudoers_handlers
from core import setup_start_handler
from app import app
from user import user
from flask import Flask, request, abort # Import Flask
import asyncio
from pyrogram import Client, errors

# Flask app initialization
web_app = Flask(__name__)

# CONNECT ALL MODULES WITH BOT AND USER CLIENT
setup_modules_handlers(app)
setup_sudoers_handlers(app)
setup_start_handler(app)

@app.on_callback_query()
async def handle_callback(client, callback_query):
    await handle_callback_query(client, callback_query)

LOGGER.info("Bot Successfully Started! 💥")

# Handle Webhook requests
@web_app.route("/", methods=["POST"])
async def telegram_webhook():
    if request.json:
        # Pass the update to Pyrogram
        async with app:
            await app.process_update(request.json)
        return "OK", 200
    else:
        abort(400)

# Set Webhook URL
async def set_webhook():
    webhook_url = f"https://worker-production-34b4.up.railway.app/" # Replace with your Railway URL
    try:
        # Use pyrogram's set_webhook method
        async with app:
            await app.set_webhook(url=webhook_url)
        LOGGER.info(f"Webhook set to {webhook_url}")
    except errors.RPCError as e:
        LOGGER.error(f"Failed to set webhook: {e}")

# Run the Flask app
if __name__ == "__main__":
    asyncio.run(set_webhook())
    web_app.run(host="0.0.0.0", port=8000)
