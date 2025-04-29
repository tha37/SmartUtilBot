# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from spellchecker import SpellChecker
from config import COMMAND_PREFIX

# Initialize the spell checker
spell = SpellChecker()

async def check_spelling(word):
    misspelled = spell.unknown([word])
    if misspelled:
        corrected_word = spell.correction(list(misspelled)[0])
    else:
        corrected_word = word
    return corrected_word

async def spell_check(client: Client, message: Message):
    user_input = message.text.split(maxsplit=1)
    if len(user_input) < 2:
        await client.send_message(message.chat.id, "**❌Provide some text to check spelling..**", parse_mode=ParseMode.MARKDOWN)
    else:
        checking_message = await client.send_message(message.chat.id, "**Checking Spelling Please Wait...✨**", parse_mode=ParseMode.MARKDOWN)
        corrected_word = await check_spelling(user_input[1])
        await checking_message.edit(text=f"`{corrected_word}`", parse_mode=ParseMode.MARKDOWN)

def setup_spl_handler(app: Client):
    app.add_handler(
        MessageHandler(
            spell_check,
            filters.command(["spell"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )