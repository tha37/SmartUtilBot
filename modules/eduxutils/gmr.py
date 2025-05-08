# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX

async def check_grammar(text):
    url = f"http://abirthetech.serv00.net/gmr.php?prompt={text}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
            return result['response'].strip()

async def grammar_check(client: Client, message: Message):
    # Check if the message is a reply
    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text.strip()
    else:
        # Check if command has text
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2:
            await client.send_message(
                message.chat.id,
                "**❌ Provide some text or reply to a message to fix grammar.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        user_input = user_input[1].strip()

    # Proceed with grammar check
    checking_message = await client.send_message(
        message.chat.id,
        "**Checking And Fixing Grammar Please Wait...✨**",
        parse_mode=ParseMode.MARKDOWN
    )
    corrected_text = await check_grammar(user_input)
    await checking_message.edit(
        text=f"{corrected_text}",
        parse_mode=ParseMode.MARKDOWN
    )

def setup_gmr_handler(app: Client):
    app.add_handler(
        MessageHandler(
            grammar_check,
            filters.command(["gra"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
