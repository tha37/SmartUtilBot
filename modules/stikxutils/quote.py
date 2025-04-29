#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import requests
import base64
import os
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType
from config import COMMAND_PREFIX, PROFILE_ERROR_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ThreadPoolExecutor instance
executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of workers

async def download_default_avatar(client, url):
    """Download default avatar from Telegram URL"""
    logger.info(f"Attempting to download default avatar from: {url}")
    
    # Check if it's a Telegram URL (t.me format)
    if "t.me/" in url:
        # Extract the chat and message ID
        parts = url.split("/")
        logger.info(f"URL parts: {parts}")
        
        if len(parts) >= 5:
            chat_username = parts[3]
            message_id = int(parts[4])
            logger.info(f"Parsed Telegram URL: chat={chat_username}, message_id={message_id}")
            
            try:
                # Get the message from Telegram
                logger.info(f"Fetching message from Telegram...")
                message = await client.get_messages(chat_username, message_id)
                
                if message and message.photo:
                    # Download the photo directly with a temporary name
                    logger.info(f"Photo found in message, downloading...")
                    temp_file = await client.download_media(message.photo.file_id)
                    logger.info(f"Downloaded to: {temp_file}")
                    return temp_file
                else:
                    logger.error(f"No photo found in message: {url}")
                    return None
            except Exception as e:
                logger.error(f"Failed to get message from Telegram: {e}")
                return None
        else:
            logger.error(f"Invalid Telegram URL format: {url}")
            return None
    else:
        # Regular URL, use requests
        try:
            logger.info(f"Downloading from regular URL...")
            response = requests.get(url)
            if response.status_code == 200:
                temp_file = f"default_avatar_{os.urandom(4).hex()}.jpg"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded to: {temp_file}")
                return temp_file
            else:
                logger.error(f"Failed to download from URL, status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading default avatar: {e}")
            return None

async def generate_quote(client: Client, message: Message):
    # Send loading message
    loading_message = await client.send_message(message.chat.id, "**Creating Custom Sticker**", parse_mode=ParseMode.MARKDOWN)
    
    command_parts = message.text.split()
    
    # Determine source of text and user
    replied_message = message.reply_to_message
    
    # Initialize variables
    text = None
    user = None
    user_id = None
    full_name = None
    avatar_file_path = None
    
    # CASE 1: Reply to message with just the command (/q) - Use replied user's profile and text
    if replied_message and len(command_parts) == 1:
        if replied_message.text:
            text = replied_message.text
            # Important: Use the replied user's profile info
            user = replied_message.from_user
        else:
            await loading_message.edit_text("**❌ The replied message must contain text.**", parse_mode=ParseMode.MARKDOWN)
            return
    
    # CASE 2: Command with text (/q some text) - Use command user's details
    elif len(command_parts) > 1:
        text = " ".join(command_parts[1:])
        user = message.from_user
    
    # CASE 3: Command with no text and no reply
    else:
        await loading_message.edit_text("**❌ Please provide text after /q or reply to a text message.**", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Get user details
    if user:
        full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
        user_id = user.id
        
        # Try to get user photo, if available
        if user.photo:
            try:
                logger.info(f"Downloading user photo for user_id: {user_id}")
                avatar_file_path = await client.download_media(user.photo.big_file_id)
                logger.info(f"User photo downloaded to: {avatar_file_path}")
            except Exception as e:
                logger.error(f"Failed to download user photo: {e}")
                avatar_file_path = None
    else:
        # Fallback to chat details if somehow user is not available
        if message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]:
            full_name = message.chat.title
            user_id = message.chat.id
            if message.chat.photo:
                try:
                    logger.info(f"Downloading chat photo for chat_id: {user_id}")
                    avatar_file_path = await client.download_media(message.chat.photo.big_file_id)
                    logger.info(f"Chat photo downloaded to: {avatar_file_path}")
                except Exception as e:
                    logger.error(f"Failed to download chat photo: {e}")
                    avatar_file_path = None
    
    # If no profile photo, use default from config
    if avatar_file_path is None:
        logger.info(f"No profile photo found, using default from PROFILE_ERROR_URL: {PROFILE_ERROR_URL}")
        # Use the default profile image from config
        avatar_file_path = await download_default_avatar(client, PROFILE_ERROR_URL)
        
        if avatar_file_path is None:
            logger.error("Failed to download default avatar")
            await loading_message.edit_text("**❌ Failed to fetch default profile image**", parse_mode=ParseMode.MARKDOWN)
            return
    
    try:
        # Convert avatar to base64
        logger.info(f"Converting avatar to base64: {avatar_file_path}")
        with open(avatar_file_path, "rb") as file:
            avatar_data = file.read()
        avatar_base64 = base64.b64encode(avatar_data).decode()
        
        # Prepare JSON data for Quotly API
        json_data = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": "#FFFFFF",
            "width": 512,
            "height": 768,
            "scale": 2,
            "messages": [
                {
                    "entities": [],
                    "avatar": True,
                    "from": {
                        "id": user_id,
                        "name": full_name,
                        "photo": {
                            "url": f"data:image/jpeg;base64,{avatar_base64}"
                        },
                        "fontSize": "small"
                    },
                    "text": text,
                    "textFontSize": "small",
                    "replyMessage": {}
                }
            ]
        }
        
        # Send API request in a non-blocking way
        logger.info("Sending request to Quotly API")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, lambda: requests.post('https://bot.lyo.su/quote/generate', json=json_data))
        
        if response.status_code != 200:
            logger.error(f"Quotly API error: {response.status_code} - {response.text}")
            raise Exception(f"API returned status code {response.status_code}")
            
        response_json = response.json()
        if 'result' not in response_json or 'image' not in response_json['result']:
            logger.error(f"Invalid response from API: {response_json}")
            raise Exception("Invalid response from API")
        
        # Process the response and generate sticker
        logger.info("Processing API response and creating sticker")
        buffer = base64.b64decode(response_json['result']['image'].encode('utf-8'))
        file_path = 'Quotly.webp'
        with open(file_path, 'wb') as f:
            f.write(buffer)
        
        # Delete loading message and send the sticker
        await loading_message.delete()
        await client.send_sticker(message.chat.id, file_path)
        logger.info("Sticker sent successfully")
    
    except Exception as e:
        # Log the error and edit loading message
        logger.error(f"Error generating quote: {e}")
        await loading_message.edit_text("**Sorry Bro Sticker Create API Dead**", parse_mode=ParseMode.MARKDOWN)
    
    finally:
        # Clean up temporary files
        logger.info("Cleaning up temporary files")
        if avatar_file_path and os.path.exists(avatar_file_path):
            os.remove(avatar_file_path)
            logger.info(f"Removed avatar file: {avatar_file_path}")
        if os.path.exists('Quotly.webp'):
            os.remove('Quotly.webp')
            logger.info("Removed sticker file")

def setup_q_handler(app: Client):
    @app.on_message(filters.command(["q", "qoute", "csticker"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def q_command(client: Client, message: Message):
        await generate_quote(client, message)