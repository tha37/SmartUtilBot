# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# Listen You Can Directly Put Values In This Config.py By Replacing "Your_{Var}_Here" Or Can Create .env And Load From There
import os
from dotenv import load_dotenv

load_dotenv()

def get_env_or_default(key, default=None, cast_func=str):
    """Helper Function For Fixing Variables By Loading Or Setting"""
    value = os.getenv(key)
    if value is not None and value.strip() != "":
        return cast_func(value)
    return default

# TELEGRAM WITH PYROGRAM MTPROTO API CONNECTION AND AUTHORIZATION SETUP
API_ID = get_env_or_default("API_ID", "Your_API_ID_Here")  # Get It From my.telegram.org
API_HASH = get_env_or_default("API_HASH", "Your_API_HASH_Here")  # Get It From my.telegram.org
BOT_TOKEN = get_env_or_default("BOT_TOKEN", "Your_BOT_TOKEN_Here")  # Get It From @BotFather
SESSION_STRING = get_env_or_default("SESSION_STRING", "Your_SESSION_STRING_Here")  # Get It From @ItsSmartToolBot And /pyro

# ADMINS AND SUDOUSERS LIST FOR BROADCAST AND OTHER SUDO WORKS METHOD 
ADMIN_IDS = get_env_or_default("ADMIN_IDS", "Your_ADMIN_IDS_Here Separate With Comma", lambda x: list(map(int, x.split(','))))  # Get It @ItsSmartToolBot And /info 
OWNER_IDS = get_env_or_default("OWNER_IDS", "Your_OWNER_IDS_Here Separate With Comma", lambda x: list(map(int, x.split(','))))  # Get It @ItsSmartToolBot And /info 

# CC SCRAPPER LIMITS FOR ALL TYPE CHAT AND GENERAL AND ADMIN LIMITS 
CC_SCRAPPER_LIMIT = get_env_or_default("CC_SCRAPPER_LIMIT", 5000, int)  # Note Limit Over 5000 May Cause Your User Acc Ban
SUDO_CCSCR_LIMIT = get_env_or_default("SUDO_CCSCR_LIMIT", 10000, int)  # Note Limit Over 5000 May Cause Your User Acc Ban
MULTI_CCSCR_LIMIT = get_env_or_default("MULTI_CCSCR_LIMIT", 2000, int) 
MAIL_SCR_LIMIT = get_env_or_default("MAIL_SCR_LIMIT", 10000, int)
SUDO_MAILSCR_LIMIT = get_env_or_default("SUDO_MAILSCR_LIMIT", 15000, int)
CC_GEN_LIMIT = get_env_or_default("CC_GEN_LIMIT", 2000, int)  # Maximum number of credit cards that can be generated
MULTI_CCGEN_LIMIT = get_env_or_default("MULTI_CCGEN_LIMIT", 5000, int)  # Maximum number of credit cards that can be generated

# MONGODB URL AND DATABASE URL FOR USER DATABASE AND GROUP SETTINGS DATABASE
MONGO_URL = get_env_or_default("MONGO_URL", "Your_MONGO_URL_Here")  # Get Him From MONGODB Website By Sign UP 
DATABASE_URL = get_env_or_default("DATABASE_URL", "Your_DATABASE_URL_Here")  # Get Him From MONGODB Website By Sign UP 
DB_URL = get_env_or_default("DB_URL", "Your_DB_URL_Here")  # Get Him From MONGODB Website By Sign UP 

# ALL PREMIUM APIS JUST FOR TOOLS SERVICES WITH AIOHTTP CLIENT METHOD AND HTTPX METHOD
GOOGLE_API_KEY = get_env_or_default("GOOGLE_API_KEY", "Your_GOOGLE_API_KEY_Here")  # Get It From Google AI Studio
MODEL_NAME = get_env_or_default("MODEL_NAME", "gemini-1.5-flash")  # Get It From Google AI Studio
GROQ_API_KEY = get_env_or_default("GROQ_API_KEY", "Your_GROQ_API_KEY_Here")  # Get It From GROQ API CONSOLE
GROQ_API_URL = get_env_or_default("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")  # Get It From GROQ API CONSOLE BY DEFAULT SET
DOMAIN_API_KEY = get_env_or_default("DOMAIN_API_KEY", "Your_DOMAIN_API_KEY_Here")  # GET FROM WHISAPI WEBSITE CONSOLE
DOMAIN_API_URL = get_env_or_default("DOMAIN_API_URL", "https://www.whoisxmlapi.com/whoisserver/WhoisService")  # GET FROM WHISAPI WEBSITE API DOCS
TEXT_MODEL = get_env_or_default("TEXT_MODEL", "deepseek-r1-distill-llama-70b")  # Get It From GROQ API CONSOLE YOUR DESIRED MODEL HERE
SPOTIFY_CLIENT_ID = get_env_or_default("SPOTIFY_CLIENT_ID", "Your_SPOTIFY_CLIENT_ID_Here")  # GET FROM SPOTIFY DEVELOPER DASHBOARD
SPOTIFY_CLIENT_SECRET = get_env_or_default("SPOTIFY_CLIENT_SECRET", "Your_SPOTIFY_CLIENT_SECRET_Here")  # GET FROM SPOTIFY DEVELOPER DASHBOARD
LOCATIONIQ_API_KEY = get_env_or_default("LOCATIONIQ_API_KEY", "Your_LOCATIONIQ_API_KEY_Here")  # GET FROM LOCATIONIQ WEBSITE 
IPINFO_API_TOKEN = get_env_or_default("IPINFO_API_TOKEN", "Your_IPINFO_API_TOKEN_Here")  # GET FROM IP INFO WEBSITE 
NEWS_API_KEY = get_env_or_default("NEWS_API_KEY", "Your_NEWS_API_KEY_Here")  # GET FROM NEWS WEBSITE SPECIFIED IN THE NEWS PLUGIN SCRIPT
BIN_KEY = get_env_or_default("BIN_KEY", "Your_BIN_KEY_Here")  # GET FROM HANDYAPI.COM JUST BY SIGN UP AND FREE 6000 CREDITS 
OPENAI_API_KEY = get_env_or_default("OPENAI_API_KEY", "Your_OPENAI_API_KEY_Here")  # GET IT FROM OPENAI API CONSOLE

# Validate OPENAI_API_KEY
if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "":
    raise ValueError("OPENAI_API_KEY is missing or empty. Please set it in .env or config.py.")

# ALL COMMANDS PREFIXES FOR ALLOWING ALL COMMANDS SUPPORT , . / ! # As Prefix 
raw_prefixes = get_env_or_default("COMMAND_PREFIX", "!|.|#|,|/")
COMMAND_PREFIX = [prefix.strip() for prefix in raw_prefixes.split("|") if prefix.strip()]  # SPECIAL FUNCTIONS FOR ALL PREFIX SUPPORT AND SPLIT WITH PIPE |

# PRINT TO VERIFY WHICH COMMAND PREFIXES LOADED AND WHICH MISSING JUST 
print("Loaded COMMAND_PREFIX:", COMMAND_PREFIX)  # JUST A KINDA HELPER FUNCTION

# Print to confirm OPENAI_API_KEY source (partially masked for security)
gpt_api_key_source = "environment variable" if os.getenv("OPENAI_API_KEY") else "config default"
print(f"OPENAI_API_KEY loaded from {gpt_api_key_source}: {'*' * 10}{OPENAI_API_KEY[-10:]}")

# FOR ENSURING THAT NO COMMAND PREFIX FOUND FROM .env
if not COMMAND_PREFIX:
    raise ValueError("Sorry Bro No Command Prefix Found First Fix It")

# THE BOT'S DEVELOPER USER ID GET IT FROM @ItsSmartToolBot
DEVELOPER_USER_ID = get_env_or_default("DEVELOPER_USER_ID", "Your_DEVELOPER_USER_ID_Here", int)  # Get It @ItsSmartToolBot And /info 

# MAX ALLOWED NUMBER OF DOMAINS TO CHECK WITH WHOISAPI RATE LIMIT MAY COME AS FREE AGENT 
DOMAIN_CHK_LIMIT = get_env_or_default("DOMAIN_CHK_LIMIT", 20, int)
PROXY_CHECK_LIMIT = get_env_or_default("PROXY_CHECK_LIMIT", 20, int)

# BOT DEVS CHANNEL URL FOR FAST REPLACEMENT FOR ANY UPDATES OF OWNER COMMUNITY
UPDATE_CHANNEL_URL = get_env_or_default("UPDATE_CHANNEL_URL", "Your_UPDATE_CHANNEL_URL_Here")  # REPLACE WITH YOUR CHANNEL URL 
PROFILE_ERROR_URL = get_env_or_default("PROFILE_ERROR_URL", "Your_PROFILE_ERROR_URL_Here")  # URL OF THE PHOTO WILL BE USED FOR USERS DONT HAVE PHOTO IN INFO COMMAND

# MAX FILE SIZE LIMIT FOR CUSTOM APIS OF OCR TOOLS AND IMGAI OF GOOGLE GEMINI LANGUAGE MODEL
IMGAI_SIZE_LIMIT = get_env_or_default("IMGAI_SIZE_LIMIT", 5242880, int)  # Keep It Unchanged Or Low For Betterment (5MB)
MAX_TXT_SIZE = get_env_or_default("MAX_TXT_SIZE", 15728640, int) 
MAX_VIDEO_SIZE = get_env_or_default("MAX_VIDEO_SIZE", 2147483648, int)

# CUSTOM GOOGLE API MODELS AND THEIR API ENDPOINT URL WITH JS AND PHP METHOD
OCR_WORKER_URL = get_env_or_default("OCR_WORKER_URL", "Your_OCR_WORKER_URL_Here")  # For Host Use PHP Cause JS Has Limit Of 100000 Request
TEXT_API_URL = get_env_or_default("TEXT_API_URL", "Your_TEXT_API_URL_Here")  # For Host Use PHP Cause JS Has Limit Of 100000 Request
IMAGE_API_URL = get_env_or_default("IMAGE_API_URL", "Your_IMAGE_API_URL_Here")  # For Host Use PHP Cause JS Has Limit Of 100000 Request 

# YOUTUBE NETSCAPE FORMAT COOKIES PATH FROM ENV IF NOT SET THEN BELOW DIRECTORY
YT_COOKIES_PATH = get_env_or_default("YT_COOKIES_PATH", "Your_YT_COOKIES_PATH_Here")  # Must Use Fresh Cookies Else YTDLP Error 

# VIDEO RESOLUTION FOR YOUTUBE DOWNLOADS
VIDEO_RESOLUTION = get_env_or_default("VIDEO_RESOLUTION", "1280x720", lambda x: tuple(map(int, x.split('x'))))  # Format: WIDTHxHEIGHT, e.g., 1280x720
