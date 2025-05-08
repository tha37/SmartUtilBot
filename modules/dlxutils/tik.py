#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import time
import re
import logging
import aiohttp
import aiofiles
import requests
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import COMMAND_PREFIX

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Progress bar function for uploads
async def progress_bar(current, total, status_message: Message, start_time, last_update_time):
    elapsed_time = time.time() - start_time
    percentage = (current / total) * 100
    progress = "▓" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
    speed = current / elapsed_time / 1024 / 1024  # Speed in MB/s
    uploaded = current / 1024 / 1024  # Uploaded size in MB
    total_size = total / 1024 / 1024  # Total size in MB

    # Throttle updates: Only update if at least 1 second has passed since the last update
    if time.time() - last_update_time[0] < 1:
        return
    last_update_time[0] = time.time()  # Update the last update time

    text = (
        f"📥 Upload Progress 📥\n\n"
        f"{progress}\n\n"
        f"🚧 Percentage: {percentage:.2f}%\n"
        f"⚡️ Speed: {speed:.2f} MB/s\n"
        f"📶 Uploaded: {uploaded:.2f} MB of {total_size:.2f} MB"
    )
    try:
        await status_message.edit(text)
    except Exception as e:
        logger.error(f"Error updating progress: {e}")

# Function to download video using the provided API
async def download_video(url, downloading_message: Message):
    api_url = "https://downloader.bot/api/tiktok/info"
    payload = {"url": url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://downloader.bot"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            logger.error(f"API error: {data['error']}")
            return None

        info = data["data"]
        video_url = info.get("mp4")
        if not video_url:
            logger.error("No video URL found in API response")
            return None

        await downloading_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
        
        video_output = "tiktok_video.mp4"
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, headers=headers) as video_response:
                if video_response.status == 200:
                    async with aiofiles.open(video_output, 'wb') as f:
                        async for chunk in video_response.content.iter_chunked(8192):
                            await f.write(chunk)
                    logger.info(f"Video downloaded successfully to: {video_output}")
                    return video_output
                else:
                    logger.error(f"Failed to download video: HTTP {video_response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return None

# Function to set up TikTok handler
def setup_tt_handler(app: Client):
    # Create a regex pattern from the COMMAND_PREFIX list
    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}tt(\s+https?://\S+)?$") & (filters.private | filters.group))
    async def tiktok_handler(client, message):
        url = None
        # Check if the message is a reply to another message containing a URL
        if message.reply_to_message and message.reply_to_message.text:
            replied_text = message.reply_to_message.text
            # Assume any text in the replied message is a potential URL
            if re.match(r'https?://\S+', replied_text):
                url = replied_text

        # If no URL from reply, check the command arguments
        if not url:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="**Please provide a TikTok link ❌**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            url = command_parts[1]

        # Step 1: Send the initial "Searching Video" message
        status_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Video...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Step 2: Download the TikTok video using the provided API
            video_path = await download_video(url, status_message)

            if not video_path:
                await status_message.edit("**❌ Invalid Video URL Inputted**")
                return

            # Step 3: Get user information
            if message.from_user:
                user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
            else:
                group_name = message.chat.title or "this group"
                group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
                user_info = f"[{group_name}]({group_url})"

            # Dummy metadata for demonstration purposes
            title = "TikTok Video"
            views = 1000
            duration_minutes = 0
            duration_seconds = 20

            # Step 4: Create the formatted message with dummy data
            caption = (
                f"🎵 **Title**: **{title}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👁️‍🗨️ **Views**: **{views} views**\n"
                f"🔗 **Url**: [Watch On TikTok]({url})\n"
                f"⏱️ **Duration**: **{duration_minutes}:{duration_seconds:02d}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**Downloaded By**: {user_info}"
            )

            # Step 5: Start uploading the video with progress
            start_time = time.time()
            last_update_time = [start_time]  # Store the last update time to throttle the progress updates

            await client.send_video(
                chat_id=message.chat.id,
                video=video_path,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                progress=progress_bar,
                progress_args=(status_message, start_time, last_update_time)
            )

            # Step 6: Delete the status message after upload starts
            await status_message.delete()

            # Clean up the downloaded video file after sending
            os.remove(video_path)
            logger.info(f"Deleted the video file: {video_path}")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            await status_message.edit("**TikTok Downloader API Dead**")
