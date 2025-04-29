import logging
import uuid
import hashlib
import time
from pyrogram import (
    Client,
    filters
)
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.raw.functions.messages import (
    SendMedia,
    SetBotPrecheckoutResults,
    SetBotShippingResults
)
from pyrogram.raw.types import (
    InputMediaInvoice,
    Invoice,
    DataJSON,
    LabeledPrice,
    UpdateBotPrecheckoutQuery,
    UpdateBotShippingQuery,
    UpdateNewMessage,
    MessageService,
    MessageActionPaymentSentMe,
    PeerUser,
    PeerChat,
    PeerChannel
)
from pyrogram.handlers import (
    MessageHandler,
    CallbackQueryHandler,
    RawUpdateHandler
)
from pyrogram.enums import ParseMode
from config import  ADMIN_IDS, DEVELOPER_USER_ID

# Setup logging
logger = logging.getLogger(__name__)

# Store active invoice requests to prevent duplicates (in-memory, replace with DB for production)
active_invoices = {}

# FUNCTION TO GET VPS UP TIME
def timeof_fmt(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

async def generate_invoice(client: Client, chat_id: int, user_id: int, quantity: int, is_callback: bool = False, callback_query: CallbackQuery = None):
    """Generate and send an invoice, editing the original message for callbacks or a new message for commands."""
    # Check for active invoice to prevent duplicates
    if active_invoices.get(user_id):
        if is_callback:
            await callback_query.answer("Donation On Progress Wait")
        else:
            await client.send_message(chat_id, "Donation On Progress Wait")
        return

    # Generate unique payload with UUID
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    invoice_payload = f"donation_{user_id}_{quantity}_{timestamp}_{unique_id}"
    request_id = int(hashlib.sha256(invoice_payload.encode()).hexdigest(), 16) % 2**63

    title = "🌟 Donation To SmartTools🌟"
    description = """
    🚀 Thank You for Powering Smart Tools! 🌟 
    Your generous donation fuels the fight against bugs 🐛 and keeps the epic vibes flowing! 😎  
    Together, we’ll conquer crashes and flex legendary status! 🏆🔥
    """
    currency = "XTR"

    try:
        active_invoices[user_id] = True

        # Determine which message to edit
        if is_callback:
            message_to_edit = callback_query.message
            await message_to_edit.edit_text("**✨ Creating Star Payment Invoice Button🌟**", parse_mode=ParseMode.MARKDOWN)
        else:
            message_to_edit = await client.send_message(chat_id, "**✨ Creating Star Payment Invoice Button🌟**", parse_mode=ParseMode.MARKDOWN)

        # Create Invoice object
        invoice = Invoice(currency=currency, prices=[LabeledPrice(label="Telegram Stars", amount=quantity)])
        payload = invoice_payload.encode()
        provider = ""
        provider_data = DataJSON(data="{}")
        media = InputMediaInvoice(
            title=title,
            description=description,
            invoice=invoice,
            payload=payload,
            provider=provider,
            provider_data=provider_data
        )
        peer = await client.resolve_peer(chat_id)

        # Send the invoice as a separate message
        await client.invoke(
            SendMedia(
                peer=peer,
                media=media,
                message="",
                random_id=request_id
            )
        )

        # Edit the message to confirmation
        confirmation_text = f"**✅ Invoice for {quantity} Stars has been generated! Please check the message below to proceed with the payment**"
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="donate")]])
        await message_to_edit.edit_text(confirmation_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button)

        if is_callback:
            await callback_query.answer("Invoice Generated! Kindly Pay Now 🌟")
        logger.info(f"Successfully sent invoice for {quantity} stars to user {user_id} with payload {invoice_payload}")
    except Exception as e:
        logger.error(f"Failed to send invoice for user {user_id}: {str(e)}")
        await message_to_edit.edit_text("Failed to generate invoice.", parse_mode=ParseMode.MARKDOWN)
        if is_callback:
            await callback_query.answer("Failed to create invoice.")
    finally:
        active_invoices.pop(user_id, None)

async def handle_donate_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    quantity = int(data.split("_")[1])  # Extract star amount (e.g., 5 from donate_5_str)
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    await generate_invoice(client, chat_id, user_id, quantity, is_callback=True, callback_query=callback_query)

async def handle_payment_command(client: Client, message: Message):
    """Handle /pay and /donate commands."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    command = message.command[0].lower()  # 'pay' or 'donate'
    args = message.command[1:]  # Arguments after the command

    if not args:
        text = """
💥 **Why should you donate to Smart Tools?** 💥
**✘ ━━━━━━━━━━━━━━━━━━ ✘**
🌟 **Love the service?** 🌟
Your support helps keep **SmartTools** fast, reliable, and free for everyone. ✨
Even a small **Donation** makes a big difference! 💖

👇 **Choose an amount to donate:** 👀

❄️ **Why donate?** ❄️
More donation = more motivation 🌐
More motivation = better tools 💫
Better tools = more productivity 🔥
More productivity = less wasted time 🇧🇩
Less wasted time = more done with **Smart Tools** 💡
**More Muhahaha… 🤓🔥**
        """
        buttons = [
            [InlineKeyboardButton("5 🌟", callback_data="donate_5_str"), InlineKeyboardButton("10 🌟", callback_data="donate_10_str"), InlineKeyboardButton("20 🌟", callback_data="donate_20_str")],
            [InlineKeyboardButton("30 🌟", callback_data="donate_30_str"), InlineKeyboardButton("50 🌟", callback_data="donate_50_str"), InlineKeyboardButton("75 🌟", callback_data="donate_75_str")],
            [InlineKeyboardButton("100 🌟", callback_data="donate_100_str"), InlineKeyboardButton("150 🌟", callback_data="donate_150_str"), InlineKeyboardButton("200 🌟", callback_data="donate_200_str")],
            [InlineKeyboardButton("⬅️ Back", callback_data="about_me")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        # Amount specified, generate invoice
        try:
            quantity = int(args[0])
            if quantity <= 0:
                await client.send_message(chat_id, "Please specify a positive integer amount.")
                return
            await generate_invoice(client, chat_id, user_id, quantity)
        except ValueError:
            await client.send_message(chat_id, "Invalid amount. Please specify an integer.")

async def raw_update_handler(client: Client, update, users, chats):
    if isinstance(update, UpdateBotPrecheckoutQuery):
        try:
            await client.invoke(
                SetBotPrecheckoutResults(
                    query_id=update.query_id,
                    success=True
                )
            )
            logger.info(f"Pre-checkout query {update.query_id} acknowledged for user {update.user_id}")
        except Exception as e:
            logger.error(f"Failed to handle pre-checkout query {update.query_id}: {str(e)}")
            await client.invoke(
                SetBotPrecheckoutResults(
                    query_id=update.query_id,
                    success=False,
                    error="Failed to process pre-checkout query."
                )
            )
    elif isinstance(update, UpdateBotShippingQuery):
        try:
            await client.invoke(
                SetBotShippingResults(
                    query_id=update.query_id,
                    shipping_options=[]  # No shipping for digital donations
                )
            )
            logger.info(f"Shipping query {update.query_id} acknowledged for user {update.user_id}")
        except Exception as e:
            logger.error(f"Failed to handle shipping query {update.query_id}: {str(e)}")
            await client.invoke(
                SetBotShippingResults(
                    query_id=update.query_id,
                    error="Shipping not required for donations."
                )
            )
    elif isinstance(update, UpdateNewMessage) and isinstance(update.message, MessageService) and isinstance(update.message.action, MessageActionPaymentSentMe):
        payment = update.message.action
        logger.debug(f"Payment message: {update.message}, from_id: {update.message.from_id}, peer_id: {update.message.peer_id}, users: {users}")

        try:
            # Extract user_id and chat_id
            user_id = update.message.from_id.user_id if update.message.from_id and hasattr(update.message.from_id, 'user_id') else None
            if not user_id and users:
                possible_user_ids = [uid for uid in users if uid > 0]
                user_id = possible_user_ids[0] if possible_user_ids else None

            if isinstance(update.message.peer_id, PeerUser):
                chat_id = update.message.peer_id.user_id
            elif isinstance(update.message.peer_id, PeerChat):
                chat_id = update.message.peer_id.chat_id
            elif isinstance(update.message.peer_id, PeerChannel):
                chat_id = update.message.peer_id.channel_id
            else:
                chat_id = None

            if not chat_id and user_id:
                chat_id = user_id  # Assume private chat

            if not user_id or not chat_id:
                raise ValueError(f"Invalid chat_id ({chat_id}) or user_id ({user_id})")

            logger.info(f"Payment successful: {payment.payload} for {payment.total_amount} {payment.currency}")

            # Get user details
            user = users.get(user_id, None)
            full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() if user else "Unknown"

            # Notify user with detailed success message
            success_text = (
                f"**✅ Hey Bruh! Donation Successful!**\n"
                f"Huge thanks **{full_name}** for donating {payment.total_amount} Stars to support Smart Tools!\n"
                f"**Your contribution helps keep everything running smooth and awesome 🚀**\n"
                f"**Transaction ID:** `{payment.charge.id}`"
            )
            await client.send_message(chat_id, success_text, parse_mode=ParseMode.MARKDOWN)

            # Notify admins
            username = f"@{user.username or 'N/A'}" if user else "@N/A"
            admin_text = (
                f"<b>🌟Hey Bruh! New Donation Received👀</b>\n"
                f"<b>✨ Donate From: </b> {full_name} 💫\n"
                f"<b>⁉️ User's ID:</b> <code>{user_id}</code>\n"
                f"<b>🌐 User's Username:</b> {username}\n"
                f"<b>💥 Donation Amount: </b> {payment.total_amount} 🌟\n"
                f"<b>Transaction ID:</b> <code>{payment.charge.id}</code>"
            )
            for admin_id in ADMIN_IDS:
                try:
                    await client.send_message(admin_id, admin_text, parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.error(f"Failed to send admin notification to {admin_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to handle successful payment for user {user_id if user_id else 'unknown'}: {str(e)}")
            if 'chat_id' in locals():
                await client.send_message(
                    chat_id,
                    "❌ Sorry Broh! Payment Declined Contact Developers",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=DEVELOPER_USER_ID)]])
                )