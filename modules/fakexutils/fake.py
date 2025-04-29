# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import pycountry
from asyncio import sleep
from config import COMMAND_PREFIX
from utils import get_locale_for_country

def setup_fake_handler(app: Client):
    @app.on_message(filters.command(["fake", "rnd"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def fake_handler(client: Client, message: Message):
        if len(message.command) <= 1:
            await client.send_message(message.chat.id, "**❌ Please Provide A Country Code**")
            return
        
        country_code = message.command[1].upper()
        country = pycountry.countries.get(alpha_2=country_code) or pycountry.countries.get(name=country_code)
        
        if not country:
            await client.send_message(message.chat.id, "**❌ Please Provide A Valid Country Code**")
            return
        
        # Fetch fake address from API for the country
        locale = get_locale_for_country(country.alpha_2) or f"{country.alpha_2.lower()}_{country.alpha_2.upper()}"
        api_url = f"https://fakerapi.it/api/v2/addresses?_quantity=1&_locale={locale}&_country_code={country.alpha_2}"
        
        generating_message = await client.send_message(message.chat.id, f"**Generating Fake Address...**")
        
        response = requests.get(api_url)
        
        if response.status_code != 200:
            await generating_message.edit_text("**Fake Address Generator API Dead**")
            return
            
        data = response.json()['data'][0]
        await generating_message.edit_text(f"""
**Address for {data['country']}**
━━━━━━━━━━━━━━━━━
**Street:** `{data['street']}`
**Street Name:** `{data['streetName']}`
**Building Number:** `{data['buildingNumber']}`
**City/Town/Village:** `{data['city']}`
**Postal code:** `{data['zipcode']}`
**Country:** `{data['country']}`
""", parse_mode=ParseMode.MARKDOWN)