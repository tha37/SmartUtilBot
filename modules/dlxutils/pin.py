# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import logging
import time
from pathlib import Path
from typing import Optional
import aiohttp
import re
import asyncio
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    TEMP_DIR = Path("temp")

Config.TEMP_DIR.mkdir(exist_ok=True)

class PinterestDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def download_media(self, url: str, downloading_message: Message) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://pin-ten-pi.vercel.app/dl?url={url}"
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=100),  # Create connector in async context
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(api_url) as response:
                    logger.info(f"API request to {api_url} returned status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"API response: {data}")
                        await downloading_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
                        media_url = data.get("dl_url")
                        title = data.get("title", "Pinterest Media")
                        filename = self.temp_dir / f"{title.replace(' ', '_')}.mp4"
                        await self._download_file(session, media_url, filename)
                        return {
                            'title': title,
                            'filename': str(filename),
                            'webpage_url': url
                        }
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Pinterest download error: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error("Request to Pinterest API timed out")
            return None

    async def _download_file(self, session: aiohttp.ClientSession, url: str, dest: Path):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    logger.info(f"Downloading media from {url} to {dest}")
                    async with aiofiles.open(dest, mode='wb') as f:
                        async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                            await f.write(chunk)
        except aiohttp.ClientError as e:
            logger.error(f"Error downloading file from {url}: {e}")
            raise

async def progress_bar(current, total, status_message, start_time, last_update_time):
    """
    Display a progress bar for uploads.
    """
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

def setup_pinterest_handler(app: Client):
    pin_downloader = PinterestDownloader(Config.TEMP_DIR)

    # Create a regex pattern from the COMMAND_PREFIX list
    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(
        filters.regex(rf"^{command_prefix_regex}(pnt|pint)(\s+https?://\S+)?$") & 
        (filters.private | filters.group)
    )
    async def pin_handler(client: Client, message: Message):
        url = None
        # Check if the message is a reply to another message
        if message.reply_to_message and message.reply_to_message.text:
            match = re.search(r"https?://pin\.it/\S+", message.reply_to_message.text)
            if match:
                url = match.group(0)
        # Check if the command includes a URL
        if not url:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) > 1:
                url = command_parts[1]

        if not url:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please provide a Pinterest link or reply to a message with a Pinterest link ❌**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        downloading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Media**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            media_info = await pin_downloader.download_media(url, downloading_message)
            if media_info:
                title = media_info['title']
                filename = media_info['filename']
                webpage_url = media_info['webpage_url']
                
                if message.from_user:
                    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                    user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
                else:
                    group_name = message.chat.title or "this group"
                    group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
                    user_info = f"[{group_name}]({group_url})"

                caption = (
                    f"🎥 **Title**: **{title}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 **Url**: [Watch On Pinterest]({webpage_url})\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"**Downloaded By**: {user_info}"
                )
                
                async with aiofiles.open(filename, 'rb'):
                    start_time = time.time()
                    last_update_time = [start_time]
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=filename,
                        supports_streaming=True,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        progress=progress_bar,
                        progress_args=(downloading_message, start_time, last_update_time)
                    )
                
                await downloading_message.delete()
                os.remove(filename)
            else:
                await downloading_message.edit_text("**Unable To Extract Url**")
        except Exception as e:
            logger.error(f"Error downloading Pinterest Media: {e}")
            await downloading_message.edit_text("**Pinterest Downloader API Dead**")
