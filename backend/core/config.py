import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve project root (…/dentistry-automation) so uvicorn --reload workers always find .env
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    # Deepgram
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Cartesia
    CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


    REDIS_URL = os.getenv("REDIS_URL")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
    UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")

    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    CLINIC_EMAIL = os.getenv("CLINIC_EMAIL")

    # Gemini (IVR navigator and any Google GenAI usage)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # App
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True") == "True"

settings = Settings()