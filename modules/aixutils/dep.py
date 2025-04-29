#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import logging
import httpx
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import GROQ_API_KEY, GROQ_API_URL, TEXT_MODEL, COMMAND_PREFIX

# Initialize logging
logger = logging.getLogger(__name__)

def setup_dep_handler(app: Client):
    @app.on_message(filters.command(["dep"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def dep_command(client: Client, message: Message):
        # Extract user text from the command
        user_text = " ".join(message.command[1:])  # Extract text after /dep
        if not user_text:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please Provide A Prompt For DeepSeekAi✨ Response**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send a temporary message
        temp_message = await client.send_message(
            chat_id=message.chat.id,
            text="**DeepSeek AI Is Thinking Wait..✨**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Call the Groq API
            response = requests.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": TEXT_MODEL,
                    "messages": [
                        {"role": "system", "content": "Reply in the same language as the user's message But Always Try To Answer Shortly"},
                        {"role": "user", "content": user_text},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            bot_response = data.get("choices", [{}])[0].get("message", {}).get("content", "Sorry DeepSeek API Dead")

            # Edit the temporary message with the final response
            await temp_message.edit_text(bot_response, parse_mode=ParseMode.MARKDOWN)

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error while calling Groq API: {e}")
            await temp_message.edit_text("**Sorry Bro DeepseekAI✨ API Dead**", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await temp_message.edit_text("**Sorry Bro DeepseekAI✨ API Dead**", parse_mode=ParseMode.MARKDOWN)