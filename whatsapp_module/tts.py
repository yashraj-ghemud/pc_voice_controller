import base64
import os
import time
import uuid
import importlib
import requests
from dotenv import load_dotenv

from .config import CONFIG


load_dotenv("env.env", override=True)
load_dotenv(override=True)


def _looks_like_mp3(audio_bytes: bytes) -> bool:
    if not audio_bytes:
        return False
    if audio_bytes.startswith(b"ID3"):
        return True
    # Typical MP3 frame sync
    if len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0:
        return True
    return False


def text_to_mp3(text: str, lang: str = "hi", out_dir: str = "temp") -> str:
    """Convert text to mp3 using Inworld Neha voice. Returns file path."""
    if not text or not text.strip():
        raise ValueError("text is empty")

    api_key = os.getenv("INWORLD_API_KEY")
    if not api_key:
        raise RuntimeError("INWORLD_API_KEY missing")

    os.makedirs(out_dir, exist_ok=True)

    payload = {
        "text": text,
        "voiceId": CONFIG["INWORLD_VOICE_ID"],
        "modelId": CONFIG["INWORLD_MODEL_ID"],
        "timestampType": "WORD",
        "audioConfig": {
            "speakingRate": CONFIG["INWORLD_SPEAKING_RATE"],
        },
        "temperature": CONFIG["INWORLD_TEMPERATURE"],
    }

    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }

    max_retries = max(1, int(CONFIG.get("TTS_MAX_RETRIES", 3)))
    min_bytes = max(512, int(CONFIG.get("TTS_MIN_BYTES", 2048)))
    last_err = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                CONFIG["INWORLD_TTS_URL"],
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            if "audioContent" not in data:
                raise RuntimeError(f"Invalid TTS response: {data}")

            audio_bytes = base64.b64decode(data["audioContent"])
            if len(audio_bytes) < min_bytes:
                raise RuntimeError(f"TTS audio too small ({len(audio_bytes)} bytes)")
            if not _looks_like_mp3(audio_bytes):
                raise RuntimeError("TTS response is not valid MP3 bytes")

            file_name = f"voice_note_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp3"
            file_path = os.path.abspath(os.path.join(out_dir, file_name))
            with open(file_path, "wb") as f:
                f.write(audio_bytes)

            # Optional deep validation if pydub is available in environment.
            try:
                pydub = importlib.import_module("pydub")
                audio_segment = getattr(pydub, "AudioSegment", None)
                if audio_segment is not None:
                    audio_segment.from_file(file_path, format="mp3")
            except Exception:
                # Do not fail hard when decoder backend is unavailable on this system.
                pass

            return file_path
        except Exception as e:
            last_err = e
            print(f"⚠️ TTS attempt {attempt}/{max_retries} failed: {e}")
            time.sleep(0.6)

    raise RuntimeError(f"Unable to generate a valid playable mp3 after retries: {last_err}")
