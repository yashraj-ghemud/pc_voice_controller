import os
import re
import time

import tts as project_tts

from .config import CONFIG
from .tts import text_to_mp3
from .clipboard import copy_file_to_clipboard
from .wa_controller import open_whatsapp_chat, paste_and_send
from .file_search import search_files
from .utils import extract_number_from_speech, listen_once


def _speak(msg: str):
    try:
        project_tts.speak_async(msg)
    except Exception:
        print(msg)


def ask_and_select_file(results: list[dict]) -> dict | None:
    """Speak results, listen for selection, return chosen file dict."""
    if not results:
        _speak("Mujhe koi file nahi mili.")
        return None

    if len(results) == 1:
        only = results[0]
        _speak(f"Mujhe ek file mili: {only['name']}. Kya yeh bheju?")
        ans = listen_once().lower()
        if any(x in ans for x in ["haan", "yes", "send", "bhejo"]):
            return only
        return None

    names = ", ".join([f"{i+1}. {r['name']}" for i, r in enumerate(results)])
    _speak(f"Mujhe {len(results)} files mili. {names}. Kaunsi bheju?")
    ans = listen_once()
    idx = extract_number_from_speech(ans)
    if idx is None or idx < 1 or idx > len(results):
        _speak("Selection samajh nahi aayi.")
        return None
    return results[idx - 1]


def _parse_send_command(command: str):
    text = (command or "").strip()

    # Example: papa ko resume bhejo
    m = re.search(r"(.+?)\s+ko\s+(.+?)\s+bhejo", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # fallback
    parts = text.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return None, None


def send_voice_note(contact_name: str, text: str) -> bool:
    """Full pipeline: TTS -> mp3 -> clipboard -> open chat -> paste -> send."""
    file_path = None
    try:
        file_path = text_to_mp3(
            text=text,
            lang=CONFIG["TTS_LANG"],
            out_dir=CONFIG["TEMP_DIR"],
        )

        if not copy_file_to_clipboard(file_path):
            return False
        if not open_whatsapp_chat(contact_name):
            return False

        # Voice notes should send immediately even while TESTING_MODE is enabled.
        paste_and_send(force_send=bool(CONFIG.get("VOICE_NOTE_FORCE_SEND", True)))

        # Keep file briefly so WhatsApp can finish attachment intake before cleanup.
        delete_delay = max(0, int(CONFIG.get("TEMP_FILE_DELETE_DELAY", 10)))
        if delete_delay > 0:
            time.sleep(delete_delay)
        return True
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


def handle_send_command(command: str) -> None:
    """
    Full handler for: 'Papa ko resume bhejo'
    Parse -> search -> show options -> listen -> send -> confirm
    """
    contact_name, keyword = _parse_send_command(command)
    if not contact_name or not keyword:
        _speak("Command samajh nahi aaya. Format bolo: papa ko resume bhejo")
        return

    results = search_files(keyword)
    chosen = ask_and_select_file(results)
    if not chosen:
        _speak("Theek hai, send cancel kar diya.")
        return

    ok = copy_file_to_clipboard(chosen["path"])
    if not ok:
        _speak("File clipboard me copy nahi ho payi.")
        return

    if not open_whatsapp_chat(contact_name):
        _speak("WhatsApp chat open nahi ho paya.")
        return

    paste_and_send()
    if CONFIG["TESTING_MODE"]:
        _speak(f"Testing mode me {chosen['name']} prepare kiya, send skip kiya.")
    else:
        _speak(f"{chosen['name']} bhej diya.")
