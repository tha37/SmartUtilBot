#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import aiohttp
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, DOMAIN_API_KEY, DOMAIN_API_URL, DOMAIN_CHK_LIMIT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def format_date(date_str):
    # Placeholder function to format date strings, implement as needed
    return date_str

async def get_domain_info(domain: str) -> str:
    params = {
        "apiKey": DOMAIN_API_KEY,
        "domainName": domain,
        "outputFormat": "JSON"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(DOMAIN_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Response for domain {domain}: {data}")  # Log the response data
                    if data.get("WhoisRecord"):
                        whois_record = data["WhoisRecord"]
                        status = whois_record.get("status", "Unknown").lower()
                        data_error = whois_record.get("dataError", "")
                        registrar = whois_record.get("registrarName", "Unknown")
                        registration_date = await format_date(whois_record.get("createdDate", "Unknown"))
                        expiration_date = await format_date(whois_record.get("expiresDate", "Unknown"))

                        if status == "available" or data_error == "MISSING_WHOIS_DATA" or not whois_record.get("registryData"):
                            return f"**✅ {domain}**: Available for registration!"
                        else:
                            return (
                                f"**🔒 {domain}**: Already registered.\n"
                                f"**Registrar:** `{registrar}`\n"
                                f"**Registration Date:** `{registration_date}`\n"
                                f"**Expiration Date:** `{expiration_date}`"
                            )
                    else:
                        return f"**✅ {domain}**: Available for registration!"
                else:
                    logger.error(f"Failed to fetch info for domain {domain}: HTTP {response.status}")
                    return f"**Sorry Bro Domain API Dead**"
    except Exception as e:
        logger.exception(f"Exception occurred while fetching info for domain {domain}")
        return f"**❌Sorry Bro Domain Check API Dead**"

async def domain_info_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Please provide at least one valid domain name.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    domains = message.command[1:]  # Extract all domains from the command
    if len(domains) > DOMAIN_CHK_LIMIT:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"**❌ You can check up to {DOMAIN_CHK_LIMIT} domains at a time.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    progress_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Fetching domain information...✨**",
        parse_mode=ParseMode.MARKDOWN
    )

    results = await asyncio.gather(*[get_domain_info(domain) for domain in domains])

    # Combine all results into a single message
    result_message = "\n\n".join(results)

    # Check if all domains are available for registration
    if all("✅" in result for result in results):
        await progress_message.edit_text(result_message, parse_mode=ParseMode.MARKDOWN)
        return

    if message.from_user:
        user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        user_info = f"\n**Domain Info Grab By:** [{user_full_name}](tg://user?id={message.from_user.id})"
    else:
        group_name = message.chat.title or "this group"
        group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
        user_info = f"\n**Domain Info Grab By:** [{group_name}]({group_url})"

    result_message += user_info

    await progress_message.edit_text(f"**Domain Check Results:**\n\n{result_message}", parse_mode=ParseMode.MARKDOWN)

def setup_dmn_handlers(app: Client):
    @app.on_message(filters.command(["dmn", ".dmn"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def domain_info(client: Client, message: Message):
        await domain_info_handler(client, message)