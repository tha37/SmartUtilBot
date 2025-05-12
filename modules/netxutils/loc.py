# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import ipaddress
import httpx  # Import httpx for asynchronous HTTP requests
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode  # Import ParseMode for Markdown formatting
from config import IPINFO_API_TOKEN, LOCATIONIQ_API_KEY, COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin from utils

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def fetch_ip_details(ip_address, client):
    try:
        ip = ipaddress.ip_address(ip_address)
        if isinstance(ip, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            url = f"https://ipinfo.io/{ip_address}?token={IPINFO_API_TOKEN}"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        else:
            raise ValueError("Invalid IP address format")
    except (ValueError, httpx.RequestError) as e:
        logger.error(f"Error fetching IP details for {ip_address}: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}loc", e, None)
        return None

def generate_static_map_url(latitude, longitude):
    try:
        # Validate latitude and longitude
        lat = float(latitude)
        lon = float(longitude)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude values")
        return f"https://maps.locationiq.com/v3/staticmap?key={LOCATIONIQ_API_KEY}&center={lat},{lon}&zoom=16&size=600x600&markers=icon:large-blue-cutout%7C{lat},{lon}"
    except (ValueError, TypeError) as e:
        logger.error(f"Error generating static map URL: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}loc", e, None)
        raise

def setup_loc_handler(app):
    @app.on_message(filters.command(["loc"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def get_ip(client, message):
        if message.from_user:
            user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
            user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
        else:
            group_name = message.chat.title or "this group"
            group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
            user_info = f"[{group_name}]({group_url})"

        ip_address = message.text[len('/loc '):].strip()
        if not ip_address:
            await client.send_message(
                message.chat.id,
                "**❌ Please provide a single IP address**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send a temporary message
        temp_msg = await client.send_message(
            message.chat.id,
            "**🔍 Fetching IP details... Please wait.**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            async with httpx.AsyncClient() as http_client:
                details = await fetch_ip_details(ip_address, http_client)
                if not details:
                    await client.edit_message_text(
                        message.chat.id,
                        temp_msg.id,
                        "**❌ Invalid IP address. Please try again.**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # Notify admins
                    await notify_admin(client, f"{COMMAND_PREFIX}loc", Exception("Invalid IP address or no details returned"), message)
                    return

                # Generate static map URL
                try:
                    map_url = generate_static_map_url(details['loc'].split(',')[0], details['loc'].split(',')[1])
                    response = await http_client.get(map_url)
                    response.raise_for_status()

                    # Prepare caption and inline keyboard (using Markdown formatting)
                    caption = f"""**🍀 Location Found 🔎**

🛰 **IP Address**: `{details['ip']}`
🌎 **Country**: `{details.get('country', 'N/A')}`
💠 **Region**: `{details.get('region', 'N/A')}`
🏠 **City**: `{details.get('city', 'N/A')}`
✉️ **Postal Code**: `{details.get('postal', 'N/A')}`
🗼 **Internet Provider**: `{details.get('org', 'N/A')}`
🕢 **Time Zone**: `{details.get('timezone', 'N/A')}`
〽️ **Location**: `{details.get('loc', 'N/A')}`

🔥 **Request By**: {user_info}"""
                    inline_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            '✈️ Open Location Via Google Map 🌎‍',
                            url=f'https://www.google.com/maps/search/?api=1&query={details["loc"].split(",")[0]}%2C{details["loc"].split(",")[1]}'
                        )]
                    ])

                    # Send photo with location details
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=map_url,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=inline_keyboard
                    )

                    # Delete the temporary message
                    await client.delete_messages(message.chat.id, temp_msg.id)

                except (httpx.RequestError, ValueError)pixel as e:
                    logger.error(f"Static map API request failed for {ip_address}: {e}")
                    # Notify admins
                    await notify_admin(client, f"{COMMAND_PREFIX}loc", e, message)
                    # Fallback to sending location directly
                    await client.send_location(
                        chat_id=message.chat.id,
                        latitude=float(details['loc'].split(',')[0]),
                        longitude=float(details['loc'].split(',')[1])
                    )
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )

                    # Edit the temporary message to indicate fallback
                    await client.edit_message_text(
                        message.chat.id,
                        temp_msg.id,
                        "**⚠️ Static Map API Dead Showing Directly**",
                        parse_mode=ParseMode.MARKDOWN
                    )

        except Exception as e:
            logger.error(f"Error processing location for {ip_address}: {e}")
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}loc", e, message)
            # Send user-facing error message
            await client.edit_message_text(
                message.chat.id,
                temp_msg.id,
                "**❌ Sorry Bro Location API Dead**",
                parse_mode=ParseMode.MARKDOWN
            )
