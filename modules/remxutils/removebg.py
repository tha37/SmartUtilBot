#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from rembg import remove
from PIL import Image
from utils import enhance_resolution
from config import COMMAND_PREFIX

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_bg_handler(app: Client):
    @app.on_message(filters.command(["bg", "rembg"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def bg_command(client, message: Message):
        try:
            # Log command usage
            logger.info(f"Command received from user {message.from_user.id} in chat {message.chat.id}")

            # Check if the message is a reply to a photo
            if message.reply_to_message and message.reply_to_message.photo:
                # Send processing message
                processing_msg = await client.send_message(
                    chat_id=message.chat.id,
                    text=" **Processing Your Image...✨**",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("Processing image...")

                # Download the image
                image_path = await message.reply_to_message.download()
                logger.info(f"Image downloaded to {image_path}")

                # Remove background
                output_path = "output.png"
                with open(image_path, "rb") as input_file:
                    with open(output_path, "wb") as output_file:
                        input_image = input_file.read()
                        output_image = remove(input_image)
                        output_file.write(output_image)
                logger.info("Background removed successfully")

                # Enhance resolution
                high_res_path = "high_res_output.png"
                enhance_resolution(output_path, high_res_path)
                logger.info("Resolution enhanced successfully")

                # Delete processing message
                await processing_msg.delete()
                logger.info("Processing message deleted")

                # Send the processed image
                await client.send_document(
                    chat_id=message.chat.id,
                    document=high_res_path,
                    caption="✅ **Here is your image with the background removed and resolution enhanced!** 🎨✨",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info("Processed image sent to user")

                # Clean up temporary files
                os.remove(image_path)
                os.remove(output_path)
                os.remove(high_res_path)
                logger.info("Temporary files deleted")

            else:
                # Notify user if no image is replied to
                await client.send_message(
                    chat_id=message.chat.id,
                    text=" **Please reply to an image with `/bg` command.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.warning("User did not reply to an image")

        except Exception as e:
            # Log the error
            logger.error(f"An error occurred: {e}", exc_info=True)
            # Edit processing message with the error message
            await processing_msg.edit_text(" **Sorry Bro, BG Remover API Dead.**")