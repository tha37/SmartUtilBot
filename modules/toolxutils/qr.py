#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp  # Import aiohttp for asynchronous HTTP requests
import asyncio
from config import COMMAND_PREFIX

async def fetch_qr_image(qr_url: str):
    # Create an asynchronous HTTP session to fetch the QR code image URL
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.teleservices.io/QR/?message={qr_url}&logo=https://abirthetech.serv00.net/abir.jpg&body=dot&eye=frame2&eyeBall=ball5&gradientColor1=%2300FF29&gradientColor2=%23000000&gradientType=gradient&gradientOnEyes=false&file=png"
        ) as response:
            if response.status == 200:
                return await response.json()  # Return the JSON response
            else:
                raise Exception(f"Failed to fetch QR code: {response.status}")

def setup_qr_handler(app):
    @app.on_message(filters.command(["qr"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def qr_dl(client: Client, message: Message):
        ID = message.from_user.id
        FIRST = message.from_user.first_name or 'N/A'
        LAST = message.from_user.last_name or ''
        qr_url = message.text[len('/qr '):]

        # Check if QR URL is too short (less than 6 characters)
        if len(qr_url) < 6:
            await message.reply(
                '<b>Please provide a QR text!</b>'
            )
            return

        # Send an initial message to inform the user the process is happening
        mafia = await message.reply("<b>Fetching QR link details...✨</b>")

        try:
            # Fetch QR image details asynchronously
            qr_data = await fetch_qr_image(qr_url)
            qr_pic = qr_data["qrImageUrl"]
            ms = qr_data["message"]

            # Send the QR code image to the chat
            await client.send_photo(
                chat_id=message.chat.id,
                photo=qr_pic,
                caption=f'''
<strong><b>🔍 QR Details 📋</b>
<b>━━━━━━━━━━━━━━━━━━</b>
<b>• Message: </b><code>{ms}</code>
<b>• File Type: </b><code>PNG</code>

<b>↠ Requested By: </b><a href="tg://user?id={ID}">{FIRST} {LAST}</a></strong>
'''
            )
            # Delete the "Fetching" message
            await mafia.delete()

        except Exception as e:
            # Update with error message if something goes wrong
            await mafia.edit(f"<b>Qr Code Gen API Dead</b>")
