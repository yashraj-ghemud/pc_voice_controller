"""
config.py — Central configuration for the Voice Assistant.
Loads environment variables and exposes all constants.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(override=True)

# ─── Gemini API Keys (supports rotation) ─────────────────────────────────────
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
]
GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k]

GEMINI_MODEL = "gemini-2.5-flash"
MAX_HISTORY_MESSAGES = 10  # Only keep the last 5 exchanges (10 messages) to save tokens


# ─── Inworld AI TTS ──────────────────────────────────────────────────────────
INWORLD_API_KEY = os.getenv("INWORLD_API_KEY")
INWORLD_TTS_URL = "https://api.inworld.ai/tts/v1/voice"
INWORLD_VOICE_ID = "default-5s-jukkvfx169axixzqasw__rrr"
INWORLD_MODEL_ID = "inworld-tts-1.5-max"
INWORLD_WORKSPACE_ID = "default-5s-jukkvfx169axixzqasw"

# ─── Assistant Personality ────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a personal AI voice assistant and who gives vibes like girlfriend. Your name is fiona.
You ALWAYS respond in hindi or hinglish but in Hindi using Devanagari script (e.g. "हाँ बोलो").
You can mix in common English words naturally like a real Indian would (Hinglish style), but write them in Devanagari too.
Talk like a real Indian girl friend — casual, expressive, and natural.
Don't use emojis, markdown formatting, or special characters in your responses.
strictly give in proper devnagri hindi language.
Sound human, not robotic. Be conversational and desi."""
