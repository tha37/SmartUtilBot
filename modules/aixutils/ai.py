#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import io
import logging
import requests
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX

API_URL = "https://abirthetech.serv00.net/ai.php"

def setup_ai_handler(app: Client):
    @app.on_message(filters.command(["ai"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gemi_handler(client: Client, message: Message):
        loading_message = None
        try:
            loading_message = await client.send_message(message.chat.id, "**🔍 Smart AI ✨ is thinking... Please wait! ✨**")

            # Check if the message contains a prompt
            if len(message.text.strip()) <= 5:
                await client.edit_message_text(message.chat.id, loading_message.id, "**Please Provide A Prompt For SmartAi✨ Response**")
                return

            # Extract the prompt from the message
            prompt = message.text.split(maxsplit=1)[1]

            # Send the prompt to the custom API and get the response
            response = requests.get(API_URL, params={"prompt": prompt})
            response_data = response.json()
            response_text = response_data["response"]

            if len(response_text) > 4000:
                parts = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
                for part in parts:
                    await client.send_message(message.chat.id, part)
            else:
                await client.edit_message_text(message.chat.id, loading_message.id, response_text)

        except Exception as e:
            logging.error(f"Error during text generation: {e}")
            if loading_message:
                await client.edit_message_text(message.chat.id, loading_message.id, "**🔍 Smart AI ✨ API Dead**")

