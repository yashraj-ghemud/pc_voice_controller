import os
import base64
import time
import threading
import requests
import io
import pygame
from dotenv import load_dotenv

# Load environment variables
load_dotenv("env.env", override=True)
load_dotenv(override=True)

# --- Inworld AI TTS Config ---
INWORLD_API_KEY = os.getenv("INWORLD_API_KEY")
INWORLD_TTS_URL = "https://api.inworld.ai/tts/v1/voice"
INWORLD_VOICE_ID = "default-5s-jukkvfx169axixzqasw__nehaaa"
INWORLD_MODEL_ID = "inworld-tts-1.5-max"
TALKING_SPEED = 1

HEADERS = {
    "Authorization": f"Basic {INWORLD_API_KEY}",
    "Content-Type": "application/json",
}

# Init pygame mixer once
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    print(f"✅ [TTS] Inworld voice loaded: {INWORLD_VOICE_ID}")
except Exception as e:
    print(f"❌ [TTS] pygame init failed: {e}")


_speak_lock = threading.Lock()


def _split_text(text, max_chars=500):
    """Split long text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""
    sentences = text.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|")

    for sentence in sentences:
        if len(current) + len(sentence) <= max_chars:
            current += sentence + " "
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence + " "

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text]


def speak(text):
    """Convert text to speech using Inworld AI cloned voice and play it."""
    if not text:
        return

    if not INWORLD_API_KEY:
        print("❌ Inworld API Key missing in env.env")
        return

    print(f"🗣️ Speaking: {text}")

    with _speak_lock:
        for chunk in _split_text(text):
            try:
                payload = {
                    "text": chunk,
                    "voiceId": INWORLD_VOICE_ID,
                    "modelId": INWORLD_MODEL_ID,
                    "talkingSpeed": TALKING_SPEED,
                    "timestampType": "WORD",
                }

                response = requests.post(INWORLD_TTS_URL, json=payload, headers=HEADERS, timeout=30)
                response.raise_for_status()

                audio_content = base64.b64decode(response.json()["audioContent"])

                # --- IN-MEMORY PROCESSING (NO FILES SAVED) ---
                audio_data = io.BytesIO(audio_content)

                # Play audio directly from memory
                try:
                    pygame.mixer.music.load(audio_data)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                    pygame.mixer.music.unload()
                except Exception as e:
                    print(f"❌ Audio Playback Error: {e}")

            except requests.exceptions.HTTPError as e:
                print(f"❌ TTS API Error: {e}")
                if e.response is not None:
                    print(f"   Response: {e.response.text}")
            except Exception as e:
                print(f"❌ TTS Error: {e}")


def speak_async(text):
    """Start speaking in background so actions can run simultaneously."""
    if not text:
        return
    worker = threading.Thread(target=speak, args=(text,), daemon=True)
    worker.start()
