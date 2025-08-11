#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, errors
from flask import Flask, request, abort
from utils import LOGGER
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN
)

# Initialize Flask app
web_app = Flask(__name__)

# Initialize Pyrogram Client
app = Client(
    "SmartTools",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000
)

# Handle incoming updates from Telegram
@web_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def handle_update():
    if request.json:
        # Pass the update to Pyrogram
        update = request.json
        try:
            await app.process_update(update)
        except errors.RPCError as e:
            LOGGER.error(f"Error processing update: {e}")
            abort(500)
    return "OK", 200

# Set Webhook on app startup
def set_webhook():
    webhook_url = f"https://your-app-name.railway.app/{BOT_TOKEN}" # Replace with your Railway app URL
    try:
        app.set_webhook(url=webhook_url)
        LOGGER.info(f"Webhook set to {webhook_url}")
    except errors.RPCError as e:
        LOGGER.error(f"Failed to set webhook: {e}")

# Run the Flask app
if __name__ == "__main__":
    app.start()
    set_webhook()
    web_app.run(host="0.0.0.0", port=8000) # Use the port assigned by Railway
