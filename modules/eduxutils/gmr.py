# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX

async def check_grammar(text):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': text,
        'language': 'en-US'
    }
    response = requests.post(url, data=data)
    result = response.json()
    corrected_text = text
    for match in result['matches']:
        offset = match['offset']
        length = match['length']
        replacement = match['replacements'][0]['value'] if match['replacements'] else ''
        corrected_text = corrected_text[:offset] + replacement + corrected_text[offset + length:]
    return corrected_text

async def grammar_check(client: Client, message: Message):
    user_input = message.text.split(maxsplit=1)
    if len(user_input) < 2:
        await client.send_message(message.chat.id, "**❌ Provide some text to fix Grammar..**", parse_mode=ParseMode.MARKDOWN)
    else:
        checking_message = await client.send_message(message.chat.id, "**Checking Grammar Please Wait...✨**", parse_mode=ParseMode.MARKDOWN)
        corrected_text = await check_grammar(user_input[1])
        await checking_message.edit(text=f"`{corrected_text}`", parse_mode=ParseMode.MARKDOWN)

def setup_gmr_handler(app: Client):
    app.add_handler(
        MessageHandler(
            grammar_check,
            filters.command(["gra"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )