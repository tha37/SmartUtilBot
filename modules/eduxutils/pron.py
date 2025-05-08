# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX

async def fetch_pronunciation_info(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            try:
                result = await response.json()
            except ValueError:
                return None
            if not result or isinstance(result, dict):
                return None
            data = result[0]
            definition = data['meanings'][0]['definitions'][0]['definition']
            stems = [meaning['partOfSpeech'] for meaning in data['meanings']]
            audio_link = None
            for phonetic in data['phonetics']:
                if phonetic['audio']:
                    audio_link = phonetic['audio']
                    break
            pronunciation_info = {
                "word": word.capitalize(),
                "breakdown": word,
                "pronunciation": "",
                "stems": stems,
                "definition": definition,
                "audio_link": audio_link
            }
            return pronunciation_info

async def pronunciation_check(client: Client, message: Message):
    # Check if the message is a reply
    if message.reply_to_message and message.reply_to_message.text:
        word = message.reply_to_message.text.strip()
        # Ensure reply contains a single word
        if len(word.split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Reply to a message with a single word to check pronunciation.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    else:
        # Check if command has a single word
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2 or len(user_input[1].split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Provide a single word to check pronunciation.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        word = user_input[1].strip()

    checking_message = await client.send_message(
        message.chat.id,
        "**Checking Pronunciation...**",
        parse_mode=ParseMode.MARKDOWN
    )
    pronunciation_info = await fetch_pronunciation_info(word)
    if pronunciation_info is None:
        await checking_message.edit(
            text="**Sorry Bro Pronunciation API Dead**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    audio_filename = None
    if pronunciation_info['audio_link']:
        audio_filename = f"{word}.mp3"
        async with aiohttp.ClientSession() as session:
            async with session.get(pronunciation_info['audio_link']) as response:
                with open(audio_filename, 'wb') as f:
                    f.write(await response.read())

    caption = (
        f"Word: {pronunciation_info['word']}\n"
        f"- Breakdown: {pronunciation_info['breakdown']}\n"
        f"- Pronunciation: {pronunciation_info['pronunciation']}\n\n"
        f"Word Stems:\n{', '.join(pronunciation_info['stems'])}\n\n"
        f"Definition:\n{pronunciation_info['definition']}"
    )

    if audio_filename:
        await client.send_audio(
            chat_id=message.chat.id,
            audio=audio_filename,
            caption=caption
        )
        os.remove(audio_filename)
    else:
        await client.send_message(
            message.chat.id,
            caption,
            parse_mode=ParseMode.MARKDOWN
        )
    await checking_message.delete()

def setup_pron_handler(app: Client):
    app.add_handler(
        MessageHandler(
            pronunciation_check,
            filters.command(["prn"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
