import os
import time
import requests
import logging
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

def enhance_image(image_path: str) -> str:
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Upload to Imglarger
        upload_url = "https://photoai.imglarger.com/api/PhoAi/Upload"
        boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
        
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": f"multipart/form-data; boundary={boundary}",
            "referer": "https://image-enhancer-snowy.vercel.app/"
        }
        
        payload = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="type"\r\n\r\n'
            f"2\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="scaleRadio"\r\n\r\n'
            f"1\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="image.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

        response = requests.post(upload_url, headers=headers, data=payload)
        response.raise_for_status()
        upload_data = response.json()
        
        if not upload_data.get('data', {}).get('code'):
            return "Error: No code received in upload response."
            
        code = upload_data['data']['code']
        
        # Check status
        status_url = "https://photoai.imglarger.com/api/PhoAi/CheckStatus"
        status_headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "referer": "https://image-enhancer-snowy.vercel.app/"
        }
        
        for _ in range(20):  # Max 20 attempts
            status_payload = {"type": "2", "code": code}
            status_response = requests.post(status_url, headers=status_headers, json=status_payload)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data.get('data', {}).get('downloadUrls', []):
                download_url = status_data['data']['downloadUrls'][0]
                if download_url.startswith(f"https://photoai.imglarger.com/color-enhancer/{code}.jpg"):
                    return download_url
            
            time.sleep(3)
            
        return "Error: Image processing timed out."
        
    except Exception as e:
        logger.error(f"Image enhancement failed: {str(e)}")
        return f"Error: {str(e)}"

def setup_remini_handler(app: Client):
    @app.on_message(filters.command(["colorize", "enhance"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def enhance_command_handler(client: Client, message: Message):
        
        if not message.reply_to_message:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please Reply To A Photo To Enhance!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not message.reply_to_message.photo:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please Reply A To A Valid Photo To Enhance!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        processing_msg = await client.send_message(
            chat_id=message.chat.id,
            text="** SmartEnhancer Enhancing Your Image..**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            logger.info(f"Enhancing image for user {message.from_user.id}")
            file_path = await client.download_media(message.reply_to_message)
            enhanced_url = enhance_image(file_path)
            
            if enhanced_url.startswith("http"):
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_url,
                    caption="✅ **Here Is Your Enhanced Image!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"Successfully enhanced image for user {message.from_user.id}")
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ **Remini Enhancer API Dead**",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.warning(f"Enhancement failed for user {message.from_user.id}: {enhanced_url}")
                
        except Exception as e:
            error_msg = f"❌ **Remini Enhancer API Dead**"
            await client.send_message(
                chat_id=message.chat.id,
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.error(f"Error in enhance_command_handler: {str(e)}")
        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            try:
                await client.delete_messages(
                    chat_id=message.chat.id,
                    message_ids=processing_msg.id
                )
            except Exception as e:
                logger.warning(f"Could not delete processing message: {str(e)}")