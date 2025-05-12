#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import requests
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import NEWS_API_KEY, COMMAND_PREFIX
import logging
import pycountry
from utils import notify_admin  # Import notify_admin

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to get country name from country code
def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name if country else country_code.upper()
    except Exception:
        return country_code.upper()

# Fetch news from the NewsData API
def fetch_news(country_code, page_token=None):
    url = f"https://newsdata.io/api/1/news?country={country_code}&apikey={NEWS_API_KEY}"
    if page_token:
        url += f"&page={page_token}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        response_json = response.json()
        logger.info(f"Fetched news: {response_json}")
        if response_json.get("status") == "error":
            raise ValueError(response_json.get("results", {}).get("message", "Error fetching news"))
        return response_json
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching news: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise

# Send news in a formatted message with pagination
async def send_news(client, chat_id, data, country_code, prev_page_token=None, next_page_token=None, message_id=None):
    news_list = data.get("results", [])
    if not news_list:
        await client.edit_message_text(
            chat_id,
            message_id,
            "**Google News API Dead**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    text = "**Top Headlines**\n"
    for news in news_list:
        title = news.get('title', 'No title')
        source_name = news.get('source_name', 'Unknown source')
        pub_date = news.get('pubDate', 'Unknown date')
        link = news.get('link', '#')
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"📰 **Title:** {title}\n"
        text += f"🏢 **Source:** {source_name}\n"
        text += f"⏰ **Publish At:** {pub_date}\n"
        text += f"🔗 [Read More]({link})\n\n"

    buttons = []
    if prev_page_token:
        buttons.append(InlineKeyboardButton("Previous", callback_data=f"{country_code}_prev_{prev_page_token}"))
    if next_page_token:
        buttons.append(InlineKeyboardButton("Next", callback_data=f"{country_code}_next_{next_page_token}"))

    reply_markup = InlineKeyboardMarkup([buttons])
    if message_id:
        await client.edit_message_text(
            chat_id,
            message_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await client.send_message(
            chat_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN
        )

# Setup news handlers
def setup_news_handler(app):
    @app.on_message(filters.command(["news"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def news(client, message):
        temp_message = None
        try:
            country_code = message.command[1].lower()
            logger.info(f"Received country code: {country_code}")
            # Send temporary "Searching" message
            country_name = get_country_name(country_code)
            temp_message = await client.send_message(
                message.chat.id,
                f"**Searching News For {country_name}**",
                parse_mode=ParseMode.MARKDOWN
            )
            # Fetch news
            data = fetch_news(country_code)
            next_page_token = data.get("nextPage")
            # Edit temporary message with news
            await send_news(client, message.chat.id, data, country_code, next_page_token=next_page_token, message_id=temp_message.id)
        except IndexError:
            await client.send_message(
                message.chat.id,
                "**Please provide a valid country code**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error handling news command: {e}")
            error_msg = "**News API Database Error**"
            # Notify admins of error
            await notify_admin(client, "/news", e, message)
            # Edit temporary message with error
            if 'temp_message' in locals():
                await client.edit_message_text(
                    message.chat.id,
                    temp_message.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    message.chat.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )

    @app.on_callback_query(filters.regex(r"(\w+)_prev_(.+)"))
    async def prev_page(client, callback_query):
        temp_message = None
        try:
            country_code, prev_page_token = callback_query.data.split("_")[0], callback_query.data.split("_")[2]
            logger(clock_query.data.split("_")[2]
            logger.info(f"Handling previous page: {country_code}, {prev_page_token}")
            # Send temporary "Searching" message
            country_name = get_country_name(country_code)
            temp_message = await client.send_message(
                callback_query.message.chat.id,
                f"**Searching News For {country_name}**",
                parse_mode=ParseMode.MARKDOWN
            )
            # Fetch news
            data = fetch_news(country_code, prev_page_token)
            next_page_token = data.get("nextPage")
            # Edit temporary message with news
            await send_news(
                client,
                callback_query.message.chat.id,
                data,
                country_code,
                prev_page_token,
                next_page_token,
                temp_message.id
            )
        except Exception as e:
            logger.error(f"Error handling previous page: {e}")
            error_msg = "**News API Database Error**"
            # Notify admins of error
            await notify_admin(client, "news_prev", e, callback_query.message)
            # Edit temporary message with error
            if 'temp_message' in locals():
                await client.edit_message_text(
                    callback_query.message.chat.id,
                    temp_message.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    callback_query.message.chat.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )

    @app.on_callback_query(filters.regex(r"(\w+)_next_(.+)"))
    async def next_page(client, callback_query):
        temp_message = None
        try:
            country_code, next_page_token = callback_query.data.split("_")[0], callback_query.data.split("_")[2]
            logger.info(f"Handling next page: {country_code}, {next_page_token}")
            # Send temporary "Searching" message
            country_name = get_country_name(country_code)
            temp_message = await client.send_message(
                callback_query.message.chat.id,
                f"**Searching News For {country_name}**",
                parse_mode=ParseMode.MARKDOWN
            )
            # Fetch news
            data = fetch_news(country_code, next_page_token)
            prev_page_token = callback_query.data.split("_")[2]  # Use the current token as the previous token for the next fetch
            # Edit temporary message with news
            await send_news(
                client,
                callback_query.message.chat.id,
                data,
                country_code,
                prev_page_token,
                data.get("nextPage"),
                temp_message.id
            )
        except Exception as e:
            logger.error(f"Error handling next page: {e}")
            error_msg = "**News API Database Error**"
            # Notify admins of error
            await notify_admin(client, "news_next", e, callback_query.message)
            # Edit temporary message with error
            if 'temp_message' in locals():
                await client.edit_message_text(
                    callback_query.message.chat.id,
                    temp_message.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    callback_query.message.chat.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
