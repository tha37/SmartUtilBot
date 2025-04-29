#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import logging
import requests
import subprocess
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, COMMAND_PREFIX
bot_token=BOT_TOKEN

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Function to get sticker set details
async def get_sticker_set(bot_token: str, name: str):
    url = f"https://api.telegram.org/bot{bot_token}/getStickerSet"
    response = requests.get(url, params={"name": name})
    return response.json().get("result") if response.status_code == 200 else None

# Function to add a PNG sticker to an existing set
async def add_sticker_to_set(bot_token: str, user_id: int, name: str, png_sticker: str, emojis: str):
    url = f"https://api.telegram.org/bot{bot_token}/addStickerToSet"
    with open(png_sticker, "rb") as sticker_file:
        response = requests.post(url, files={"png_sticker": sticker_file}, data={"user_id": user_id, "name": name, "emojis": emojis})
    if response.status_code != 200:
        raise Exception(response.json()["description"])

# Function to add a video sticker
async def add_video_sticker_to_set(bot_token: str, user_id: int, name: str, webm_sticker: str, emojis: str):
    url = f"https://api.telegram.org/bot{bot_token}/addStickerToSet"
    with open(webm_sticker, "rb") as sticker_file:
        response = requests.post(url, files={"webm_sticker": sticker_file}, data={"user_id": user_id, "name": name, "emojis": emojis})
    if response.status_code != 200:
        raise Exception(response.json()["description"])

# Function to create a new sticker set
async def create_sticker_set(bot_token: str, user_id: int, name: str, title: str, png_sticker: str, emojis: str):
    url = f"https://api.telegram.org/bot{bot_token}/createNewStickerSet"
    with open(png_sticker, "rb") as sticker_file:
        response = requests.post(url, files={"png_sticker": sticker_file}, data={"user_id": user_id, "name": name, "title": title, "emojis": emojis})
    if response.status_code != 200:
        raise Exception(response.json()["description"])

# Function to process video stickers
async def process_video_sticker(input_file: str, output_file: str):
    try:
        command = [
            "ffmpeg", "-i", input_file,
            "-vf", "scale=512:-1",
            "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "256k",
            "-an",
            output_file
        ]
        subprocess.run(command, check=True)
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {str(e)}")
        return None

# Setup the /kang command
def setup_kang_handler(app: Client, bot_token: str):
    @app.on_message(filters.command(["kang"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def kang(client: Client, message: Message):
        user = message.from_user
        packnum = 1
        packname = f"a{user.id}_by_{client.me.username}"
        max_stickers = 120

        temp_message = await message.reply_text("<b>Kanging this Sticker...✨</b>")

        # Find an available sticker pack
        while True:
            sticker_set = await get_sticker_set(bot_token, packname)
            if sticker_set and len(sticker_set["stickers"]) >= max_stickers:
                packnum += 1
                packname = f"a{packnum}_{user.id}_by_{client.me.username}"
            else:
                break

        if not message.reply_to_message:
            await temp_message.edit_text("<b>Please reply to a sticker, image, or document to kang it!</b>")
            return

        # Get file ID
        reply = message.reply_to_message
        if reply.sticker:
            file_id = reply.sticker.file_id
        elif reply.photo:
            file_id = reply.photo.file_id
        elif reply.document:
            file_id = reply.document.file_id
        else:
            await temp_message.edit_text("<b>Sticker Kang API Dead</b>")
            return

        # Download file
        sticker_format = "png"
        if reply.sticker and reply.sticker.is_animated:
            kang_file = await app.download_media(file_id, file_name="kangsticker.tgs")
            sticker_format = "tgs"
        elif reply.sticker and reply.sticker.is_video:
            kang_file = await app.download_media(file_id, file_name="kangsticker.webm")
            sticker_format = "webm"
        else:
            kang_file = await app.download_media(file_id, file_name="kangsticker.png")

        # Select emoji
        sticker_emoji = "🌟"
        if len(message.command) > 1:
            sticker_emoji = message.command[1]
        elif reply.sticker and reply.sticker.emoji:
            sticker_emoji = reply.sticker.emoji

        # Resize PNG if needed
        if sticker_format == "png":
            try:
                im = Image.open(kang_file)
                if max(im.width, im.height) > 512:
                    im.thumbnail((512, 512))
                im.save(kang_file, "PNG")
            except Exception as e:
                await temp_message.edit_text(f"<b>Sticker Kang API Dead</b> {e}")
                return

        # Process video sticker
        if sticker_format == "webm":
            temp_output = "compressed.webm"
            processed_file = await process_video_sticker(kang_file, temp_output)

            if not processed_file:
                await temp_message.edit_text("<b>Video Sticker API Dead</b>")
                return

            kang_file = temp_output

        # Add sticker to the pack
        try:
            if sticker_format == "webm":
                await add_video_sticker_to_set(bot_token, user.id, packname, kang_file, sticker_emoji)
            else:
                await add_sticker_to_set(bot_token, user.id, packname, kang_file, sticker_emoji)

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View Sticker Pack", url=f"t.me/addstickers/{packname}")]])
            await temp_message.edit_text(f"<b>Sticker successfully added!</b>\n<b>Emoji:</b> {sticker_emoji}", reply_markup=keyboard)

        except Exception as e:
            if "STICKERSET_INVALID" in str(e):
                # Create a new sticker pack
                pack_title = f"{user.first_name}'s Sticker Pack"
                try:
                    await create_sticker_set(bot_token, user.id, packname, pack_title, kang_file, sticker_emoji)
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View Sticker Pack", url=f"t.me/addstickers/{packname}")]])
                    await temp_message.edit_text(f"<b>New sticker pack created!</b>\n<b>Emoji:</b> {sticker_emoji}", reply_markup=keyboard)
                except Exception as ce:
                    await temp_message.edit_text(f"<b>Sticker Kang API Dead</b>")
            else:
                await temp_message.edit_text(f"<b>Sticker Kang API Dead</b>")

        # Cleanup downloaded file
        if os.path.exists(kang_file):
            os.remove(kang_file)