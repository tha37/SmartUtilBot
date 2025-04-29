#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, YT_COOKIES_PATH

async def ytag_handler(client: Client, message: Message):
    if len(message.command) <= 1:
        await client.send_message(
            message.chat.id, 
            "**❌ Please provide a YouTube URL. Usage: /ytag [URL]**", 
            parse_mode=ParseMode.MARKDOWN, 
            disable_web_page_preview=True
        )
        return

    url = message.command[1]
    fetching_msg = await client.send_message(
        message.chat.id, 
        "**Processing Your Request...**", 
        parse_mode=ParseMode.MARKDOWN, 
        disable_web_page_preview=True
    )
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'cookiefile': YT_COOKIES_PATH,  # Correct path to your cookie file
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            tags = info_dict.get('tags', [])

        if not tags:
            response = "**Sorry, no tags available for this video.**"
        else:
            tags_str = "\n".join([f"`{tag}`" for tag in tags])
            response = f"**Your Requested Video Tags ✅**\n━━━━━━━━━━━━━━━━\n{tags_str}"

    except Exception as e:
        response = f"**An error occurred: {str(e)}**"

    await fetching_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


# Function to set up handlers for the Pyrogram bot
def setup_ytag_handlers(app: Client):

    @app.on_message(filters.command(["ytag", ".ytag"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def ytag_info(client: Client, message: Message):
        await ytag_handler(client, message)