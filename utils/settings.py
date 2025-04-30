#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode
import os
import re
from dotenv import load_dotenv
from config import COMMAND_PREFIX, ADMIN_IDS

# Load environment variables
load_dotenv()

# Temporary storage for tracking user actions
user_session = {}

# Helper function to detect duplicate keys in the `.env` file
def detect_duplicate_keys():
    """Log a warning for duplicate keys in the .env file."""
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
            print(f"Warning: Duplicate keys found in .env: {', '.join(duplicates)}")

detect_duplicate_keys()

# Helper function to load environment variables
def load_env_vars():
    """Load all unique environment variables from the .env file."""
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
        return variables

def update_env_var(key, value):
    """Update a specific environment variable in the .env file."""
    env_vars = load_env_vars()
    env_vars[key] = value
    with open(".env", "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

config_keys = load_env_vars()
ITEMS_PER_PAGE = 10  # Show 10 variables per page (5 rows)

# Regex patterns for validation
VALIDATION_PATTERNS = {
    "API_ID": r"^\d+$",  # API_ID must be numeric
    "API_HASH": r"^[a-f0-9]{32}$",  # API_HASH must be a valid 32-character hexadecimal string
    "BOT_TOKEN": r"^\d+:[a-zA-Z0-9_-]+$",  # BOT_TOKEN must follow Telegram's bot token format
    "DEFAULT_LIMIT": r"^\d+$",  # DEFAULT_LIMIT must be numeric
    "ADMIN_LIMIT": r"^\d+$",  # ADMIN_LIMIT must be numeric
    "COMMAND_PREFIX": r"^[!#.,|]+$",  # COMMAND_PREFIX must be a combination of specific characters
    "DEVELOPER_USER_ID": r"^\d+$",  # DEVELOPER_USER_ID must be numeric
}

def is_valid_value(key, value):
    """Validate the value for a given key using predefined regex patterns."""
    pattern = VALIDATION_PATTERNS.get(key)
    if pattern:
        return bool(re.match(pattern, value))
    return True  # If no pattern is defined, assume the value is valid.

def build_menu(page=0):
    """Build the inline keyboard menu for settings."""
    keys = list(config_keys.keys())  # Extract unique keys from config_keys dictionary
    start, end = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
    current_keys = keys[start:end]

    rows = []
    for i in range(0, len(current_keys), 2):  # Two buttons per row
        buttons = [
            InlineKeyboardButton(current_keys[i], callback_data=f"settings_edit_{current_keys[i]}")
        ]
        if i + 1 < len(current_keys):  # Add a second button if available
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

def setup_settings_handler(app: Client):
    """Setup the settings handler for the Pyrogram app."""

    @app.on_message(filters.command(["settings"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def show_settings(client, message: Message):
        """Show the settings menu."""
        # Restrict to admins only
        if message.from_user.id not in ADMIN_IDS:
            await client.send_message(
                chat_id=message.chat.id,
                text="**🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️**"
            )
            return

        await client.send_message(
            chat_id=message.chat.id,
            text="**Select a variable to edit 👇**",
            reply_markup=build_menu()
        )

    @app.on_callback_query(filters.regex(r"^settings_page_(\d+)$"))
    async def paginate_menu(client, callback_query: CallbackQuery):
        """Handle pagination in the settings menu."""
        # Restrict to admins
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️", show_alert=True)
            return

        page = int(callback_query.data.split("_")[2])
        await callback_query.edit_message_reply_markup(reply_markup=build_menu(page))
        await callback_query.answer()

    @app.on_callback_query(filters.regex(r"^settings_edit_(.+)"))
    async def edit_var(client, callback_query: CallbackQuery):
        """Handle the selection of a variable to edit."""
        # Restrict to admins
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️", show_alert=True)
            return

        var_name = callback_query.data.split("_", 2)[2]
        if var_name not in config_keys:
            await callback_query.answer("Invalid variable selected.", show_alert=True)
            return

        # Store user action in user_session
        user_session[callback_query.from_user.id] = {"var": var_name}
        await callback_query.edit_message_text(
            text=f"**Editing `{var_name}`. Please send the new value below.**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="settings_cancel_edit")]])
        )

    @app.on_callback_query(filters.regex(r"^settings_cancel_edit$"))
    async def cancel_edit(client, callback_query: CallbackQuery):
        """Cancel the editing process."""
        # Restrict to admins
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️", show_alert=True)
            return

        # Remove user from session
        user_session.pop(callback_query.from_user.id, None)
        await callback_query.edit_message_text("**Variable Editing Cancelled**")
        await callback_query.answer()

    @app.on_message(filters.text & ~filters.command("settings"))
    async def update_value(client, message: Message):
        """Update the value of a selected variable."""
        # Restrict to admins
        if message.from_user.id not in ADMIN_IDS:
            await client.send_message(
                chat_id=message.chat.id,
                text="**🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️**"
            )
            return

        session = user_session.get(message.from_user.id)
        if session:
            var, val = session["var"], message.text

            # Validate the value
            if not is_valid_value(var, val):
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"**Invalid value provided. Please try again. ❌**"
                )
                return

            # Update the .env file
            update_env_var(var, val)
            # Update the in-memory config_keys
            config_keys[var] = val
            # Notify the user of the successful update
            await client.send_message(
                chat_id=message.chat.id,
                text=f"**`{var}` has been successfully updated to `{val}`. ✅**"
            )
            # Cleanup session
            user_session.pop(message.from_user.id, None)
            # Reload environment variables
            load_dotenv(override=True)

    @app.on_callback_query(filters.regex(r"^settings_closesettings$"))
    async def close_menu(client, callback_query: CallbackQuery):
        """Close the settings menu."""
        # Restrict to admins
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️", show_alert=True)
            return

        await callback_query.edit_message_text("**Settings Menu Closed Successfully ✅**")
        await callback_query.answer()
