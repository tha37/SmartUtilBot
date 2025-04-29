#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
import re
from config import COMMAND_PREFIX

def youtube_parser(url):
    # Regular expression to extract YouTube video ID from various URL formats
    reg_exp = r"(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})"
    match = re.search(reg_exp, url)
    return match.group(1) if match else False

async def handle_yth_command(client: Client, message: Message):
    if len(message.command) == 1:
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>❌ Provide a Valid YouTube link</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        youtube_url = message.command[1]
        video_id = youtube_parser(youtube_url)
        if not video_id:
            await client.send_message(
                chat_id=message.chat.id,
                text="<b>Invalid YouTube link Bro ❌</b>",
                parse_mode=ParseMode.HTML
            )
            return
        
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        caption = "<code>Photo Sent</code>"
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=thumbnail_url,
            caption=caption,
            parse_mode=ParseMode.HTML
        )

def setup_yth_handler(app: Client):
    @app.on_message(filters.command("yth", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def yth_command(client: Client, message: Message):
        await handle_yth_command(client, message)