import os
from dotenv import load_dotenv
load_dotenv()

CONFIG = {
    # API Keys
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    "OPENAI_API_BASE": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    "HF_API_KEY": os.getenv("HF_API_KEY", ""),
    "HF_MODEL_ID": os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2"),
    "HUGGINGFACE_API_BASE": os.getenv("HUGGINGFACE_API_BASE"),
    "OPENAI_MODEL": "gpt-4o-mini",

    # Assistant
    "ASSISTANT_NAME": os.getenv("ASSISTANT_NAME", "Nova"),
    "USE_OPENAI": os.getenv("USE_OPENAI", "true").lower() in ("true", "1", "yes"),
    "MAX_HISTORY_MESSAGES": int(os.getenv("MAX_HISTORY_MESSAGES", "12")),

    # Voice engine settings
    "VOICE_ENGINE": os.getenv("VOICE_ENGINE", "pyttsx3"),
    "VOICE_RATE": int(os.getenv("VOICE_RATE", "200")),
    "VOLUME": float(os.getenv("VOLUME", "1.0")),
    "LANGUAGE": os.getenv("LANGUAGE", "en-in"),

    # PostgreSQL DB
    "DB_HOST": os.getenv("DB_HOST"),
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_USER": os.getenv("DB_USER"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),

    # Runtime only
    "CURRENT_USER": None
}
