# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import COMMAND_PREFIX
from typing import Tuple, List

# Function to fetch synonyms and antonyms using Datamuse API
async def fetch_synonyms_antonyms(word: str) -> Tuple[List[str], List[str]]:
    async with aiohttp.ClientSession() as session:
        synonyms_url = f"https://api.datamuse.com/words?rel_syn={word}"
        antonyms_url = f"https://api.datamuse.com/words?rel_ant={word}"
        
        async with session.get(synonyms_url) as syn_response, session.get(antonyms_url) as ant_response:
            synonyms = [syn['word'] for syn in await syn_response.json()]
            antonyms = [ant['word'] for ant in await ant_response.json()]
    
    return synonyms, antonyms

def setup_syn_handler(app: Client):
    @app.on_message(filters.command(["syn", "synonym"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def synonyms_handler(client: Client, message: Message):
        # Check if the message is a reply
        if message.reply_to_message and message.reply_to_message.text:
            word = message.reply_to_message.text.strip()
            # Ensure reply contains a single word
            if len(word.split()) != 1:
                await client.send_message(
                    message.chat.id,
                    "**❌ Reply to a message with a single word to get synonyms and antonyms.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        else:
            # Check if command has a single word
            if len(message.command) <= 1 or len(message.command[1].split()) != 1:
                await client.send_message(
                    message.chat.id,
                    "**❌ Provide a single word to get synonyms and antonyms.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            word = message.command[1].strip()

        loading_message = await client.send_message(
            message.chat.id,
            "**Fetching Synonyms and Antonyms...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            synonyms, antonyms = await fetch_synonyms_antonyms(word)
            synonyms_text = ", ".join(synonyms) if synonyms else "No synonyms found"
            antonyms_text = ", ".join(antonyms) if antonyms else "No antonyms found"

            response_text = (
                f"**Synonyms:**\n{synonyms_text}\n\n"
                f"**Antonyms:**\n{antonyms_text}"
            )

            await loading_message.edit(response_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await loading_message.edit(
                "**Synonym Antonym API Dead**",
                parse_mode=ParseMode.MARKDOWN
            )
