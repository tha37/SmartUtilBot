# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import logging
import requests
import subprocess
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, COMMAND_PREFIX

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Function to get sticker set details
async def get_sticker_set(bot_token: str, name: str):
    url = f"https://api.telegram.org/bot{bot_token}/getStickerSet"
    response = requests.get(url, params={"name": name})
    if response.status_code != 200:
        logger.error(f"Failed to get sticker set: {response.json()}")
    return response.json().get("result") if response.status_code == 200 else None

# Function to add a PNG sticker to an existing set
async def add_sticker_to_set(bot_token: str, user_id: int, name: str, png_sticker: str, emojis: str):
    url = f"https://api.telegram.org/bot{bot_token}/addStickerToSet"
    with open(png_sticker, "rb") as sticker_file:
        response = requests.post(url, files={"png_sticker": sticker_file}, 
                               data={"user_id": user_id, "name": name, "emojis": emojis})
    if response.status_code != 200:
        logger.error(f"Failed to add PNG sticker: {response.json()}")
        raise Exception(response.json()["description"])
    return response.json()

# Function to add a video sticker
async def add_video_sticker_to_set(bot_token: str, user_id: int, name: str, webm_sticker: str, emojis: str):
    url = f"https://api.telegram.org/bot{bot_token}/addStickerToSet"
    with open(webm_sticker, "rb") as sticker_file:
        response = requests.post(url, files={"webm_sticker": sticker_file}, 
                               data={"user_id": user_id, "name": name, "emojis": emojis})
    if response.status_code != 200:
        logger.error(f"Failed to add video sticker: {response.json()}")
        raise Exception(response.json()["description"])
    return response.json()

# Function to add an animated sticker
async def add_animated_sticker_to_set(bot_token: str, user_id: int, name: str, tgs_sticker: str, emojis: str):
    url = f"https://api.telegram.org/bot{bot_token}/addStickerToSet"
    with open(tgs_sticker, "rb") as sticker_file:
        response = requests.post(url, files={"tgs_sticker": sticker_file}, 
                               data={"user_id": user_id, "name": name, "emojis": emojis})
    if response.status_code != 200:
        logger.error(f"Failed to add animated sticker: {response.json()}")
        raise Exception(response.json()["description"])
    return response.json()

# Function to create a new sticker set
async def create_sticker_set(bot_token: str, user_id: int, name: str, title: str, sticker_file: str, emojis: str, sticker_type: str):
    url = f"https://api.telegram.org/bot{bot_token}/createNewStickerSet"
    file_param = "png_sticker" if sticker_type == "png" else "tgs_sticker" if sticker_type == "tgs" else "webm_sticker"
    with open(sticker_file, "rb") as sticker_file:
        response = requests.post(url, files={file_param: sticker_file}, 
                               data={"user_id": user_id, "name": name, "title": title, "emojis": emojis})
    if response.status_code != 200:
        logger.error(f"Failed to create sticker set: {response.json()}")
        raise Exception(response.json()["description"])
    return response.json()

# Function to process video stickers
async def process_video_sticker(input_file: str, output_file: str):
    try:
        # Trim to 3 seconds, scale to 512x512, optimize bitrate and frame rate
        command = [
            "ffmpeg", "-i", input_file,
            "-t", "3",  # Limit duration to 3 seconds
            "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2,fps=30",
            "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "200k",  # Lower bitrate for smaller file
            "-an", "-y",  # Remove audio and overwrite output
            output_file
        ]
        subprocess.run(command, check=True, capture_output=True)
        # Check file size (max 256KB)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 256 * 1024:
            logger.warning("File size exceeds 256KB, re-encoding with lower quality")
            command = [
                "ffmpeg", "-i", input_file,
                "-t", "3",
                "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2,fps=24",
                "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "150k",
                "-an", "-y",
                output_file
            ]
            subprocess.run(command, check=True, capture_output=True)
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {str(e)}")
        return None

# Function to process GIF to WebM
async def process_gif_to_webm(input_file: str, output_file: str):
    try:
        # Trim to 3 seconds, scale to 512x512, optimize bitrate and frame rate
        command = [
            "ffmpeg", "-i", input_file,
            "-t", "3",  # Limit duration to 3 seconds
            "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2,fps=30",
            "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "200k",
            "-an", "-y",
            output_file
        ]
        subprocess.run(command, check=True, capture_output=True)
        # Check file size (max 256KB)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 256 * 1024:
            logger.warning("File size exceeds 256KB, re-encoding with lower quality")
            command = [
                "ffmpeg", "-i", input_file,
                "-t", "3",
                "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2,fps=24",
                "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "150k",
                "-an", "-y",
                output_file
            ]
            subprocess.run(command, check=True, capture_output=True)
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {str(e)}")
        return None

# Setup the /kang command handler
def setup_kang_handler(app: Client, bot_token: str):
    logger.info(f"Setting up kang handler with bot_token: {bot_token[:10]}...")  # Log first 10 chars of token for debugging
    @app.on_message(filters.command(["kang"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def kang(client: Client, message: Message):
        user = message.from_user
        packnum = 1
        packname = f"a{user.id}_by_{client.me.username}"
        max_stickers = 120
        temp_files = []

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
        elif reply.animation:
            file_id = reply.animation.file_id
        else:
            await temp_message.edit_text("<b>Please reply to a valid sticker, image, GIF, or document!</b>")
            return

        # Determine sticker format
        sticker_format = "png"
        if reply.sticker:
            if reply.sticker.is_animated:
                sticker_format = "tgs"
            elif reply.sticker.is_video:
                sticker_format = "webm"
        elif reply.animation or (reply.document and reply.document.mime_type == "image/gif"):
            sticker_format = "gif"

        # Download file
        try:
            if sticker_format == "tgs":
                kang_file = await app.download_media(file_id, file_name="kangsticker.tgs")
            elif sticker_format == "webm":
                kang_file = await app.download_media(file_id, file_name="kangsticker.webm")
            elif sticker_format == "gif":
                kang_file = await app.download_media(file_id, file_name="kangsticker.gif")
            else:
                kang_file = await app.download_media(file_id, file_name="kangsticker.png")
            
            if not kang_file:
                await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                return
            
            temp_files.append(kang_file)

        except Exception as e:
            await temp_message.edit_text(f"<b>❌ Failed To Kang The Sticker</b>")
            return

        # Select emoji
        sticker_emoji = "🌟"
        if len(message.command) > 1:
            sticker_emoji = message.command[1]
        elif reply.sticker and reply.sticker.emoji:
            sticker_emoji = reply.sticker.emoji

        # Process files
        try:
            if sticker_format == "png":
                im = Image.open(kang_file)
                if max(im.width, im.height) > 512:
                    im.thumbnail((512, 512))
                im.save(kang_file, "PNG")
            
            elif sticker_format == "gif":
                temp_output = "compressed.webm"
                processed_file = await process_gif_to_webm(kang_file, temp_output)
                if not processed_file:
                    await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                    return
                kang_file = temp_output
                sticker_format = "webm"
                temp_files.append(kang_file)
            
            elif sticker_format == "webm":
                temp_output = "compressed.webm"
                processed_file = await process_video_sticker(kang_file, temp_output)
                if not processed_file:
                    await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                    return
                kang_file = temp_output
                temp_files.append(kang_file)

        except Exception as e:
            await temp_message.edit_text(f"<b>❌ Failed To Kang The Sticker</b>")
            return

        # Add sticker to the pack
        try:
            if sticker_format == "tgs":
                await add_animated_sticker_to_set(bot_token, user.id, packname, kang_file, sticker_emoji)
            elif sticker_format == "webm":
                await add_video_sticker_to_set(bot_token, user.id, packname, kang_file, sticker_emoji)
            else:
                await add_sticker_to_set(bot_token, user.id, packname, kang_file, sticker_emoji)

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View Sticker Pack", url=f"t.me/addstickers/{packname}")]])
            await temp_message.edit_text(f"<b>Sticker successfully added!</b>\n<b>Emoji:</b> {sticker_emoji}", reply_markup=keyboard)

        except Exception as e:
            if "STICKERSET_INVALID" in str(e):
                pack_title = f"{user.first_name}'s Sticker Pack"
                try:
                    await create_sticker_set(bot_token, user.id, packname, pack_title, kang_file, sticker_emoji, sticker_format)
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View Sticker Pack", url=f"t.me/addstickers/{packname}")]])
                    await temp_message.edit_text(f"<b>New sticker pack created!</b>\n<b>Emoji:</b> {sticker_emoji}", reply_markup=keyboard)
                except Exception as ce:
                    await temp_message.edit_text(f"<b>❌ Failed To Kang The Sticker</b>")
            else:
                await temp_message.edit_text(f"<b>❌ Failed To Kang The Sticker</b>")
        
        finally:
            # Cleanup all temporary files
            for file in temp_files:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except:
                        logger.warning(f"Failed to remove temporary file: {file}")
