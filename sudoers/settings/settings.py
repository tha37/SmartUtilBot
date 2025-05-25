# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode, ChatType
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
import os
from dotenv import load_dotenv
from config import COMMAND_PREFIX, OWNER_ID
from core import auth_admins
from utils import LOGGER

# Load The Environment Variables
load_dotenv()

# Temp Session For Managing User Editing State
user_session = {}

# Helper Function To Remove Duplicate VARS
def detect_duplicate_keys():
    """Log a warning for duplicate keys in the .env file."""
    try:
        with open(".env") as f:
            lines = f.readlines()
            seen_keys = set()
            duplicates = set()
            for line in lines:
                if '=' in line:
                    key = line.split("=", 1)[0].strip()
                    if key in seen_keys:
                        duplicates.add(key)
                    seen_keys.add(key)
            if duplicates:
                LOGGER.warning(f"Duplicate keys found in .env: {', '.join(duplicates)}")
    except Exception as e:
        LOGGER.error(f"Error detecting duplicate keys in .env: {e}")

detect_duplicate_keys()

# Helper function to load environment variables
def load_env_vars():
    """Load all unique environment variables from the .env file."""
    try:
        with open(".env") as f:
            lines = f.readlines()
            variables = {}
            seen_keys = set()  # Use a set to track unique keys
            for line in lines:
                if '=' in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key not in seen_keys:  # Only add unique keys
                        variables[key] = value
                        seen_keys.add(key)
            LOGGER.info("Environment variables loaded successfully")
            return variables
    except Exception as e:
        LOGGER.error(f"Error loading environment variables: {e}")
        return {}

def update_env_var(key, value):
    """Update a specific environment variable in the .env file."""
    try:
        env_vars = load_env_vars()
        env_vars[key] = value
        with open(".env", "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")
        LOGGER.info(f"Updated environment variable {key} to '{value}'")
    except Exception as e:
        LOGGER.error(f"Error updating environment variable {key}: {e}")

config_keys = load_env_vars()
ITEMS_PER_PAGE = 10  

def build_menu(page=0):
    """Build the inline keyboard menu for settings."""
    try:
        keys = list(config_keys.keys())  # Extract unique keys from config_keys dictionary
        start, end = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
        current_keys = keys[start:end]

        rows = []
        for i in range(0, len(current_keys), 2):  # Two buttons per row
            buttons = [
                InlineKeyboardButton(current_keys[i], callback_data=f"settings_edit_{current_keys[i]}")
            ]
            if i + 1 < len(current_keys):  
                buttons.append(InlineKeyboardButton(current_keys[i + 1], callback_data=f"settings_edit_{current_keys[i + 1]}"))
            rows.append(buttons)

        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"settings_page_{page - 1}"))
        if end < len(keys):
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"settings_page_{page + 1}"))
        if nav_buttons:
            if page == 0:  # For the first page, combine "Next" and "Close" buttons in the same row
                nav_buttons.append(InlineKeyboardButton("Close ❌", callback_data="settings_closesettings"))
                rows.append(nav_buttons)
            else:
                rows.append(nav_buttons)

        # Close button for other pages
        if page > 0:
            rows.append([InlineKeyboardButton("Close ❌", callback_data="settings_closesettings")])

        return InlineKeyboardMarkup(rows)
    except Exception as e:
        LOGGER.error(f"Error building settings menu: {e}")
        return InlineKeyboardMarkup([])

def setup_settings_handler(app: Client):
    """Setup the settings handler for the Pyrogram app."""
    LOGGER.info("Setting up settings handler")

    async def debug_all(client: Client, message: Message):
        """Catch-all handler to debug all group chat messages."""
        try:
            thread_id = getattr(message, "message_thread_id", None)
            is_reply = message.reply_to_message_id is not None
            LOGGER.debug(f"Catch-all: user {message.from_user.id}, chat {message.chat.id}, text='{message.text}', "
                        f"chat_type={message.chat.type}, is_reply={is_reply}, reply_to={message.reply_to_message_id}, thread={thread_id}")
        except Exception as e:
            LOGGER.error(f"Error in debug_all handler: {e}")

    async def show_settings(client: Client, message: Message):
        """Show the settings menu."""
        user_id = message.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            LOGGER.info(f"Unauthorized settings access attempt by user_id {user_id}")
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘Kids Not Allowed To Do This↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            try:
                chat = await client.get_chat(message.chat.id)
                permissions = chat.permissions
                if not permissions.can_send_messages:
                    LOGGER.error(f"Bot lacks permission to send messages in chat {message.chat.id}")
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**Sorry Bro This Group Is Restricted**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                LOGGER.debug(f"Chat {message.chat.id} permissions: can_send_messages={permissions.can_send_messages}, "
                            f"can_read_messages={getattr(permissions, 'can_read_messages', 'Unknown')}")
            except Exception as e:
                LOGGER.error(f"Failed to check permissions in chat {message.chat.id}: {e}")
                return

        LOGGER.info(f"Showing settings menu for user {user_id} in chat {message.chat.id}")
        await client.send_message(
            chat_id=message.chat.id,
            text="**Select a change or edit 👇**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_menu()
        )

    async def paginate_menu(client: Client, callback_query: CallbackQuery):
        """Handle pagination in the settings menu."""
        user_id = callback_query.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            LOGGER.info(f"Unauthorized pagination attempt by user_id {user_id}")
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        page = int(callback_query.data.split("_")[2])
        LOGGER.info(f"Paginating to page {page} for user {user_id}")
        await callback_query.edit_message_reply_markup(reply_markup=build_menu(page))
        await callback_query.answer()

    async def edit_var(client: Client, callback_query: CallbackQuery):
        """Handle the selection of a variable to edit."""
        user_id = callback_query.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            LOGGER.info(f"Unauthorized edit attempt by user_id {user_id}")
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        var_name = callback_query.data.split("_", 2)[2]
        if var_name not in config_keys:
            LOGGER.warning(f"Invalid variable selected: {var_name}")
            await callback_query.answer("Invalid variable selected.", show_alert=True)
            return

        user_session[user_id] = {
            "var": var_name,
            "chat_id": callback_query.message.chat.id
        }
        LOGGER.info(f"User {user_id} started editing {var_name} in chat {callback_query.message.chat.id}")
        await callback_query.edit_message_text(
            text=f"**Editing `{var_name}`. Please send the new value below.**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="settings_cancel_edit")]])
        )

    async def cancel_edit(client: Client, callback_query: CallbackQuery):
        """Cancel the editing process."""
        user_id = callback_query.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            LOGGER.info(f"Unauthorized cancel edit attempt by user_id {user_id}")
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        user_session.pop(user_id, None)
        LOGGER.info(f"User {user_id} cancelled editing")
        await callback_query.edit_message_text("**Variable Editing Cancelled**", parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()

    async def update_value(client: Client, message: Message):
        """Update the value of a selected variable."""
        user_id = message.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            LOGGER.info(f"Unauthorized value update attempt by user_id {user_id}")
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘Kids Not Allowed To Do This↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            user_session.pop(user_id, None)
            return

        session = user_session.get(user_id)
        if not session:
            LOGGER.debug(f"No session found for user {user_id} in chat {message.chat.id}")
            return

        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            try:
                chat = await client.get_chat(message.chat.id)
                permissions = chat.permissions
                if not permissions.can_send_messages:
                    LOGGER.error(f"Bot lacks permission to send messages in chat {message.chat.id}")
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**Sorry Bro This Group Is Restricted!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                LOGGER.debug(f"Chat {message.chat.id} permissions: can_send_messages={permissions.can_send_messages}, "
                            f"can_read_messages={getattr(permissions, 'can_read_messages', 'Unknown')}")
            except Exception as e:
                LOGGER.error(f"Failed to check permissions in chat {message.chat.id}: {e}")
                return

        LOGGER.info(f"Processing value update for user {user_id} in chat {message.chat.id}, session: {session}")
        try:
            var, val = session["var"], message.text.strip()
            update_env_var(var, val)
            config_keys[var] = val
            await client.send_message(
                chat_id=message.chat.id,
                text=f"**`{var}` Has Been Successfully Updated To `{val}`. ✅**",
                parse_mode=ParseMode.MARKDOWN
            )
            user_session.pop(user_id, None)
            load_dotenv(override=True)
            LOGGER.info(f"Successfully updated {var} to '{val}' for user {user_id} in chat {message.chat.id}")
        except Exception as e:
            LOGGER.error(f"Error updating value for {var}: {e}")
            await client.send_message(
                chat_id=message.chat.id,
                text=f"**Error updating `{var}`: {e}**",
                parse_mode=ParseMode.MARKDOWN
            )

    async def close_menu(client: Client, callback_query: CallbackQuery):
        """Close the settings menu."""
        user_id = callback_query.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            LOGGER.info(f"Unauthorized menu close attempt by user_id {user_id}")
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        LOGGER.info(f"Closing settings menu for user {user_id}")
        await callback_query.edit_message_text("**Settings Menu Closed Successfully ✅**", parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()

    # Register handlers with group=1
    app.add_handler(MessageHandler(debug_all, filters.chat([ChatType.GROUP, ChatType.SUPERGROUP])), group=1)
    app.add_handler(MessageHandler(show_settings, filters.command(["settings"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)), group=1)
    app.add_handler(MessageHandler(update_value, filters.text), group=1)
    app.add_handler(CallbackQueryHandler(paginate_menu, filters.regex(r"^settings_page_(\d+)$")), group=1)
    app.add_handler(CallbackQueryHandler(edit_var, filters.regex(r"^settings_edit_(.+)")), group=1)
    app.add_handler(CallbackQueryHandler(cancel_edit, filters.regex(r"^settings_cancel_edit$")), group=1)
    app.add_handler(CallbackQueryHandler(close_menu, filters.regex(r"^settings_closesettings$")), group=1)