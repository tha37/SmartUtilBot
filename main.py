#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from misc import handle_callback_query
from utils import LOGGER
from modules import setup_modules_handlers
from sudoers import setup_sudoers_handlers
from core import setup_start_handler
from app import app
from user import user
from flask import Flask, request, abort
from pyrogram import errors
import asyncio
import requests # requests library ကို import လုပ်ပါ။
from config import BOT_TOKEN # BOT_TOKEN ကို import လုပ်ဖို့ လိုအပ်ပါတယ်။

# Flask app initialization
web_app = Flask(__name__)

# CONNECT ALL MODULES WITH BOT AND USER CLIENT
setup_modules_handlers(app)
setup_sudoers_handlers(app)
setup_start_handler(app)

@app.on_callback_query()
async def handle_callback(client, callback_query):
    await handle_callback_query(client, callback_query)

# Handle Webhook requests
@web_app.route("/", methods=["POST"])
async def telegram_webhook():
    if request.json:
        # Pass the update to Pyrogram
        try:
            await app.process_update(request.json)
        except errors.RPCError as e:
            LOGGER.error(f"Error processing update: {e}")
            abort(500)
    return "OK", 200

# Webhook URL ကို set လုပ်ဖို့အတွက် ပြင်ဆင်ထားတဲ့ function
def set_webhook():
    webhook_url = f"https://worker-production-34b4.up.railway.app/" # သင့်ရဲ့ Railway App URL ကိုထည့်ပါ။
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, data={'url': webhook_url})
        if response.status_code == 200:
            LOGGER.info(f"Webhook set to {webhook_url}")
        else:
            LOGGER.error(f"Failed to set webhook. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        LOGGER.error(f"Error setting webhook: {e}")

# This part needs to be simplified to avoid multiple loops
if __name__ == "__main__":
    # Start the Pyrogram client first
    app.start()
    
    # Set the webhook synchronously (without asyncio)
    set_webhook()
    
    # Run the Flask app
    web_app.run(host="0.0.0.0", port=8000)
    
    # Finally, stop the pyrogram client
    app.stop()
