# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from googletrans import Translator, LANGUAGES
from config import COMMAND_PREFIX

# Initialize the Google Translator
translator = Translator()

def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language using Google Translate API."""
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception:
        raise

def setup_tr_handler(app: Client):
    @app.on_message(filters.command(["tr", "translate"] + [f"tr{code}" for code in LANGUAGES.keys()], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def translate_handler(client: Client, message: Message):
        """Handle translation requests with both formats:
        1. /tr en text (space separated)
        2. /tren text (combined command)
        """
        combined_format = message.command[0][2:] in LANGUAGES  # Check if part after /tr is a language code
        
        if message.reply_to_message and message.reply_to_message.text:
            if combined_format:
                target_lang = message.command[0][2:].lower()
                text_to_translate = message.reply_to_message.text
            else:
                if len(message.command) < 2:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**❌ Bro! That's not a valid language code!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                target_lang = message.command[1].lower()
                text_to_translate = message.reply_to_message.text
        else:
            if combined_format:
                if len(message.command) < 2:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**❌ Bro! That's not a valid language code!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                target_lang = message.command[0][2:].lower()
                text_to_translate = " ".join(message.command[1:])
            else:
                if len(message.command) < 3:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**❌ Bro! That's not a valid language code!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                target_lang = message.command[1].lower()
                text_to_translate = " ".join(message.command[2:])

        if target_lang not in LANGUAGES:
            await client.send_message(
                chat_id=message.chat.id,
                text=(f"**❌ Bro! That Is Not A Valid Language Code**"),
                parse_mode=ParseMode.MARKDOWN
            )
            return

        loading_message = await client.send_message(
            chat_id=message.chat.id,
            text=f"**Translating Your Text Into ({target_lang})...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            translated_text = translate_text(text_to_translate, target_lang)
            response_text = f"`{translated_text}`"
            await loading_message.edit(response_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await loading_message.edit(text="**❌ Google Translate API Dead **", parse_mode=ParseMode.MARKDOWN)