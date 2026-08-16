"""
╔══════════════════════════════════════════════════════════════╗
║           KYPZER — AI Voice PC Assistant                     ║
║           All modules combined into one file                 ║
║                                                              ║
║  Sections:                                                   ║
║    1. Imports & Environment Setup                            ║
║    2. STT  — Speech-to-Text                                  ║
║    3. MIC  — Microphone Recording                            ║
║    4. TTS  — Text-to-Speech (Inworld AIo)                     ║
║    5. SCREEN AI — Vision-based UI automation (Groq/LLaMA)   ║
║    6. ACTIONS — All PC automation actions                    ║
║    7. INTENT — Offline intent classifier (Hindi/English)     ║
║    8. MEMORY — Vector DB conversation memory (ChromaDB)      ║
║    9. BRAIN — Gemini AI processing core                      ║
║   10. MAIN — Entry point / main loop                         ║
╚══════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS & ENVIRONMENT SETUP
# ══════════════════════════════════════════════════════════════

import os
import re
import io
import json
import time
import wave
import base64
import ctypes
import random
import subprocess
import webbrowser
import platform

# Third-party
import pyaudio
import pyautogui
import keyboard
import requests
import pygame
import mss
from PIL import Image
from groq import Groq
from dotenv import load_dotenv
from google import genai
from AppOpener import open as app_open, close as app_close
import speech_recognition as sr

# Optional heavy imports (loaded lazily where needed)
try:
    import chromadb
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False
    print("⚠️ chromadb not installed — memory features disabled. Run: pip install chromadb")

try:
    import pyperclip
    _PYPERCLIP_AVAILABLE = True
except ImportError:
    _PYPERCLIP_AVAILABLE = False
    print("⚠️ pyperclip not installed. Run: pip install pyperclip")

# ── Load .env ──────────────────────────────────────────────────
load_dotenv("env.env", override=True)
load_dotenv(override=True)

# Disable pyautogui's built-in pause for faster execution
pyautogui.PAUSE = 0.02

# DPI awareness fix on Windows (prevents coordinate mismatches with display scaling)
if os.name == "nt":
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# SECTION 2 — STT (Speech-to-Text)
# ══════════════════════════════════════════════════════════════

def transcribe_wav_google(audio_path: str, language: str = "en-IN"):
    """
    Transcribe a WAV file using Google's free online Web Speech API.

    Returns:
        (text, error) — one of them will be None.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=language)
        return text, None
    except sr.UnknownValueError:
        return None, "Speech was not clear enough to transcribe."
    except sr.RequestError as e:
        return None, f"Speech recognition request failed: {e}"
    except Exception as e:
        return None, f"Speech recognition error: {e}"


# ══════════════════════════════════════════════════════════════
# SECTION 3 — MIC (Microphone Recording)
# ══════════════════════════════════════════════════════════════

_MIC_CHUNK        = 1024
_MIC_FORMAT       = pyaudio.paInt16
_MIC_CHANNELS     = 1
_MIC_RATE         = 44100
_MIC_RECORD_SECS  = 5
_MIC_OUTPUT_FILE  = "input.wav"


def listen_voice(timeout=8, phrase_time_limit=10):
    """
    Listen for voice input using SpeechRecognition's built-in VAD.
    Automatically starts when speech is detected and stops on silence.

    Returns:
        (audio_file_path, None) on success
        (None, error_string) on failure
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold      = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold        = 1.5

    try:
        with sr.Microphone(sample_rate=_MIC_RATE) as source:
            print("🎤 Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🟢 Listening... (speak now)")
            try:
                audio = recognizer.listen(source, timeout=timeout,
                                          phrase_time_limit=phrase_time_limit)
                print("✅ Voice captured!")
            except sr.WaitTimeoutError:
                return None, "timeout"

        wav_data = audio.get_wav_data(convert_rate=_MIC_RATE, convert_width=2)
        with open(_MIC_OUTPUT_FILE, "wb") as f:
            f.write(wav_data)
        return _MIC_OUTPUT_FILE, None

    except Exception as e:
        print(f"❌ Mic error: {e}")
        return None, str(e)


def record_audio(output_filename=_MIC_OUTPUT_FILE, record_seconds=_MIC_RECORD_SECS):
    """
    Fallback: Record audio for a fixed duration from the default microphone.
    """
    p = pyaudio.PyAudio()
    print(f"🎤 Listening... (Recording for {record_seconds}s)")
    try:
        stream = p.open(format=_MIC_FORMAT, channels=_MIC_CHANNELS,
                        rate=_MIC_RATE, input=True,
                        frames_per_buffer=_MIC_CHUNK)
        frames = [stream.read(_MIC_CHUNK)
                  for _ in range(int(_MIC_RATE / _MIC_CHUNK * record_seconds))]
        print("✅ Recording finished.")
        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(_MIC_CHANNELS)
            wf.setsampwidth(p.get_sample_size(_MIC_FORMAT))
            wf.setframerate(_MIC_RATE)
            wf.writeframes(b''.join(frames))
        return output_filename
    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        p.terminate()
        return None


# ══════════════════════════════════════════════════════════════
# SECTION 4 — TTS (Text-to-Speech via Inworld AI)
# ══════════════════════════════════════════════════════════════

_INWORLD_API_KEY  = os.getenv("INWORLD_API_KEY")
_INWORLD_TTS_URL  = "https://api.inworld.ai/tts/v1/voice"
_INWORLD_VOICE_ID = "default-5s-jukkvfx169axixzqasw__nehaaa"
_INWORLD_MODEL_ID = "inworld-tts-1.5-max"
_INWORLD_SPEAKING_RATE = 1
_INWORLD_TEMPERATURE   = 1.01

_TTS_HEADERS = {
    "Authorization": f"Basic {_INWORLD_API_KEY}",
    "Content-Type":  "application/json",
}

try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    print(f"✅ [TTS] Inworld voice loaded: {_INWORLD_VOICE_ID}")
except Exception as _e:
    print(f"❌ [TTS] pygame init failed: {_e}")


def _tts_split_text(text, max_chars=500):
    """Split long text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks, current = [], ""
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
    return chunks or [text]


def speak(text):
    """Convert text to speech using Inworld AI cloned voice and play it."""
    if not text:
        return
    if not _INWORLD_API_KEY:
        print("❌ Inworld API Key missing in env.env")
        return

    print(f"🗣️ Speaking: {text}")
    for chunk in _tts_split_text(text):
        try:
            payload = {
                "text":         chunk,
                "voiceId":      _INWORLD_VOICE_ID,
                "modelId":      _INWORLD_MODEL_ID,
                "timestampType": "WORD",
                "audioConfig": {"speakingRate": _INWORLD_SPEAKING_RATE},
                "temperature": _INWORLD_TEMPERATURE,
            }
            response = requests.post(_INWORLD_TTS_URL, json=payload,
                                     headers=_TTS_HEADERS, timeout=30)
            response.raise_for_status()
            audio_content = base64.b64decode(response.json()["audioContent"])
            audio_data = io.BytesIO(audio_content)
            try:
                pygame.mixer.music.load(audio_data, "mp3")
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


# ══════════════════════════════════════════════════════════════
# SECTION 5 — SCREEN AI (Vision-based UI automation via Groq)
# ══════════════════════════════════════════════════════════════

_SCREEN_AI_API_KEY   = "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"
_SCREEN_AI_CLIENT    = Groq(api_key=_SCREEN_AI_API_KEY)
_SCREEN_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
_last_screenshot_size = None


def take_screenshot():
    """Take a full screenshot and return a base64-encoded JPEG string."""
    global _last_screenshot_size
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        img = sct.grab(monitor)
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        _last_screenshot_size = pil_img.size
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=70)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")


def _get_screen_dimensions():
    """Return actual screen dimensions as (width, height)."""
    with mss.mss() as sct:
        m = sct.monitors[0]
        return m["width"], m["height"]


def ask_about_screenshot(question, b64_image):
    """Send a question + screenshot to Groq Vision model and return the text answer."""
    completion = _SCREEN_AI_CLIENT.chat.completions.create(
        model=_SCREEN_VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
            ],
        }],
    )
    return completion.choices[0].message.content


def find_element_coordinates(description, b64_image=None):
    """
    Use vision AI to find a UI element on screen and return its (x, y) coordinates.

    Args:
        description: Natural language description, e.g. "search bar", "play button".
        b64_image:   Optional pre-captured screenshot. Takes a fresh one if None.

    Returns:
        (x, y) tuple, or None if not found.
    """
    if b64_image is None:
        b64_image = take_screenshot()
    screen_w, screen_h = _get_screen_dimensions()

    prompt = (
        f'Look at this screenshot carefully. Find the UI element: "{description}"\n\n'
        f"The screen resolution is {screen_w}x{screen_h} pixels.\n\n"
        'Respond ONLY with JSON:\n'
        '{"x": <number>, "y": <number>, "found": true, "element": "<what you found>"}\n\n'
        'If not found:\n'
        '{"x": 0, "y": 0, "found": false, "element": "not found"}\n\n'
        "Give pixel positions. Respond with ONLY the JSON, no other text."
    )

    try:
        response = ask_about_screenshot(prompt, b64_image)
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            if data.get("found", False):
                x = max(0, min(int(data["x"]), screen_w - 1))
                y = max(0, min(int(data["y"]), screen_h - 1))
                print(f"👁️ Found '{description}' at ({x}, {y}) — {data.get('element', '')}")
                return (x, y)
            else:
                print(f"👁️ Could not find '{description}' on screen")
                return None
        else:
            print(f"⚠️ Vision AI returned unparseable response: {response[:200]}")
            return None
    except Exception as e:
        print(f"❌ Screen AI error: {e}")
        return None


def find_and_click_element(description):
    """Take a screenshot, find the described element, and click it."""
    print(f"🔍 Looking for '{description}' on screen...")
    b64_image = take_screenshot()
    coords = find_element_coordinates(description, b64_image)
    if coords:
        x, y = coords
        print(f"🖱️ Clicking at ({x}, {y})...")
        pyautogui.click(x, y)
        time.sleep(0.3)
        return True
    print(f"❌ Could not find '{description}' to click")
    return False


def find_and_type_in_field(text, field_description="text input field or search bar",
                           press_enter=True):
    """
    Take a screenshot, find an input field, click it, type text,
    and optionally press Enter.
    """
    print(f"🔍 Looking for input field: '{field_description}'...")
    b64_image = take_screenshot()
    coords = find_element_coordinates(field_description, b64_image)
    if coords:
        x, y = coords
        print(f"🖱️ Clicking input field at ({x}, {y})...")
        pyautogui.click(x, y)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        print(f"⌨️ Typing: {text}")
        if _PYPERCLIP_AVAILABLE:
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(text, interval=0.03)
        time.sleep(0.3)
        if press_enter:
            print("⏎ Pressing Enter...")
            pyautogui.press('enter')
            time.sleep(0.3)
        return True
    print(f"❌ Could not find input field: '{field_description}'")
    return False


def analyze_screen(question=None):
    """
    Take a screenshot and analyze what's currently on screen.
    If question is None, gives a general overview.
    """
    b64_image = take_screenshot()
    question = question or (
        "Describe what is currently visible on this screen. "
        "What applications are open? What is the user looking at? Be concise."
    )
    try:
        return ask_about_screenshot(question, b64_image)
    except Exception as e:
        return f"Error analyzing screen: {e}"


def check_visual_condition(condition_description, b64_image=None):
    """
    Ask the vision model whether a UI condition is met on the current screen.

    Returns:
        dict: {"met": bool, "reason": str}
    """
    if b64_image is None:
        b64_image = take_screenshot()

    prompt = (
        f"You are checking whether a UI condition is currently true.\n\n"
        f"Condition to verify: {condition_description}\n\n"
        'Respond with ONLY valid JSON:\n'
        '{"met": true/false, "reason": "short reason"}\n\n'
        "Use met=true only if the condition is clearly visible. "
        "If uncertain, use met=false. Return ONLY JSON, no extra text."
    )

    try:
        response = ask_about_screenshot(prompt, b64_image)
        json_match = re.search(r'\{[^{}]*\}', response)
        if not json_match:
            return {"met": False, "reason": "unparseable response"}
        data = json.loads(json_match.group())
        return {"met": bool(data.get("met", False)),
                "reason": str(data.get("reason", ""))}
    except Exception as e:
        return {"met": False, "reason": f"vision error: {e}"}


def wait_for_visual_condition(condition_description, timeout=120, interval=4,
                               stable_checks=2):
    """
    Poll the screen until the condition is met for a stable number of consecutive checks.

    Returns:
        True if condition met before timeout, else False.
    """
    start       = time.time()
    consecutive = 0

    while (time.time() - start) < timeout:
        result = check_visual_condition(condition_description)
        met    = result.get("met", False)
        reason = result.get("reason", "")
        print(f"👁️ Condition check -> met={met} | reason={reason}")
        if met:
            consecutive += 1
            if consecutive >= stable_checks:
                return True
        else:
            consecutive = 0
        time.sleep(interval)
    return False


# ══════════════════════════════════════════════════════════════
# SECTION 6 — ACTIONS (All PC automation)
# ══════════════════════════════════════════════════════════════

# ── Native DPI-safe click ──────────────────────────────────────
def _native_click_at(x, y, button="left"):
    """DPI-safe native click for Windows; falls back to pyautogui elsewhere."""
    if os.name != "nt":
        pyautogui.click(x, y, button=button)
        return
    user32 = ctypes.windll.user32
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.06)
    LEFTDOWN,  LEFTUP   = 0x0002, 0x0004
    RIGHTDOWN, RIGHTUP  = 0x0008, 0x0010
    MIDDLEDOWN,MIDDLEUP = 0x0020, 0x0040
    if button == "right":
        user32.mouse_event(RIGHTDOWN, 0, 0, 0, 0); time.sleep(0.02)
        user32.mouse_event(RIGHTUP,   0, 0, 0, 0)
    elif button == "middle":
        user32.mouse_event(MIDDLEDOWN, 0, 0, 0, 0); time.sleep(0.02)
        user32.mouse_event(MIDDLEUP,   0, 0, 0, 0)
    else:
        user32.mouse_event(LEFTDOWN, 0, 0, 0, 0); time.sleep(0.02)
        user32.mouse_event(LEFTUP,   0, 0, 0, 0)


# ── Volume control (pycaw with keyboard fallback) ─────────────
_PYCAW_OK = False
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    def _get_volume_interface():
        device = AudioUtilities.GetSpeakers()
        raw    = getattr(device, '_dev', device)
        iface  = raw.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(iface, POINTER(IAudioEndpointVolume))

    _get_volume_interface()   # test once at startup
    _PYCAW_OK = True
    print("✅ [VOL] pycaw volume control ready")
except Exception as _e:
    print(f"⚠️ [VOL] pycaw not available, using keyboard fallback: {_e}")


def _normalize_level(level):
    """Convert any volume value to integer 0–100."""
    if isinstance(level, float) and level <= 1.0:
        level = int(level * 100)
    return max(0, min(100, int(level)))


def set_volume(level):
    """Set system volume to an exact percentage (0–100)."""
    level = _normalize_level(level)
    if _PYCAW_OK:
        try:
            vol = _get_volume_interface()
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            print(f"🔊 Volume set to {level}%")
            return
        except Exception as e:
            print(f"⚠️ pycaw failed, keyboard fallback: {e}")
    # Keyboard fallback
    old_pause = pyautogui.PAUSE; pyautogui.PAUSE = 0
    for _ in range(50):        pyautogui.press("volumedown")
    for _ in range(level // 2): pyautogui.press("volumeup")
    pyautogui.PAUSE = old_pause
    print(f"🔊 Volume set to ~{level}%")


def change_volume(change):
    """Change volume up/down by a relative amount."""
    try:
        steps = max(1, int(abs(change) / 2))
        key   = "volumeup" if change > 0 else "volumedown"
        for _ in range(steps):
            pyautogui.press(key)
        print(f"🔊 Volume {'increased' if change > 0 else 'decreased'}")
    except Exception as e:
        print(f"❌ Error changing volume: {e}")


def mute_volume():
    pyautogui.press("volumemute"); print("🔇 Muted")

def unmute_volume():
    pyautogui.press("volumemute"); print("🔊 Unmuted")


# ── App management ────────────────────────────────────────────
_MANUAL_APP_MAP = {
    "chrome":     "google chrome",
    "youtube":    "google chrome",
    "notepad":    "notepad",
    "calc":       "calculator",
    "calculator": "calculator",
    "vscode":     "visual studio code",
    "code":       "visual studio code",
}


def open_via_search(app_name):
    print(f"🔎 Opening {app_name} via Windows Search...")
    pyautogui.press("win"); time.sleep(0.3)
    pyautogui.write(app_name, interval=0.03); time.sleep(0.4)
    pyautogui.press("enter")


def open_application(app_name):
    print(f"🚀 Opening {app_name}...")
    search_name = _MANUAL_APP_MAP.get(app_name.lower(), app_name)
    if "chrome" in search_name.lower() or "google" in search_name.lower():
        open_via_search(search_name); return
    try:
        app_open(search_name, match_closest=True, throw_error=True)
    except Exception:
        open_via_search(search_name)


def close_application(app_name):
    print(f"🛑 Closing {app_name}...")
    try:
        app_close(app_name, match_closest=True, throw_error=True)
    except Exception:
        try:
            os.system(f"taskkill /f /im {app_name}.exe")
        except Exception as e:
            print(f"❌ Failed to close {app_name}: {e}")


# ── Web browser ───────────────────────────────────────────────
def search_web(query):
    print(f"🌍 Searching for: {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")


def open_url(url):
    print(f"🌐 Opening URL: {url}")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    webbrowser.open(url)


# ── Input control ─────────────────────────────────────────────
def type_text(text):
    print(f"⌨️ Typing: {text}")
    if _PYPERCLIP_AVAILABLE:
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
    else:
        pyautogui.write(text, interval=0.03)


def press_key(key_name):
    print(f"🎹 Pressing key: {key_name}")
    try:
        keyboard.send(key_name)
    except Exception as e:
        print(f"❌ Error pressing key {key_name}: {e}")


def click_mouse():
    pyautogui.click()


def move_mouse(x, y):
    pyautogui.moveTo(x, y)


# ── Virtual desktop switching ─────────────────────────────────
def switch_desktop_left():
    print("🖥️ Switching to LEFT desktop...")
    pyautogui.hotkey('win', 'ctrl', 'left'); time.sleep(0.8)
    print("✅ Switched to left desktop")


def switch_desktop_right():
    print("🖥️ Switching to RIGHT desktop...")
    pyautogui.hotkey('win', 'ctrl', 'right'); time.sleep(0.8)
    print("✅ Switched to right desktop")


# ── Media controls ────────────────────────────────────────────
def play_media():
    print("▶️ Playing media..."); pyautogui.press("playpause")

def pause_media():
    print("⏸️ Pausing media..."); pyautogui.press("playpause")

def next_track():
    print("⏭️ Next track..."); pyautogui.press("nexttrack")

def prev_track():
    print("⏮️ Previous track..."); pyautogui.press("prevtrack")

def stop_media():
    print("⏹️ Stopping media..."); pyautogui.press("stop")


# ── Brightness control (Windows WMI via PowerShell) ───────────
def set_brightness(level):
    level = max(0, min(100, int(level)))
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
             f".WmiSetBrightness(1,{level})"],
            capture_output=True, timeout=5,
        )
        print(f"🔆 Brightness set to {level}%")
    except Exception as e:
        print(f"❌ Brightness error: {e}")


def change_brightness(change):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"],
            capture_output=True, text=True, timeout=5,
        )
        current   = int(result.stdout.strip()) if result.stdout.strip() else 50
        new_level = max(0, min(100, current + change))
        set_brightness(new_level)
    except Exception as e:
        print(f"❌ Brightness error: {e}")


# ── WiFi control ──────────────────────────────────────────────
def wifi_on():
    try:
        subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"],
                       capture_output=True, timeout=5)
        print("📶 WiFi enabled")
    except Exception as e:
        print(f"❌ WiFi error: {e}")


def wifi_off():
    try:
        subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"],
                       capture_output=True, timeout=5)
        print("📴 WiFi disabled")
    except Exception as e:
        print(f"❌ WiFi error: {e}")


# ── Bluetooth control (PowerShell) ────────────────────────────
_BT_PS_BASE = (
    "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
    "$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,"
    "ContentType=WindowsRuntime]::GetRadiosAsync().GetAwaiter().GetResult()"
    " | Where-Object { $_.Kind -eq 'Bluetooth' }; "
)

def bluetooth_on():
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             _BT_PS_BASE + "if ($radio) { $radio.SetStateAsync('On').GetAwaiter().GetResult() }"],
            capture_output=True, timeout=10,
        )
        print("🔵 Bluetooth enabled")
    except Exception as e:
        os.system("start ms-settings:bluetooth")
        print(f"🔵 Opened Bluetooth settings (auto-toggle failed: {e})")


def bluetooth_off():
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             _BT_PS_BASE + "if ($radio) { $radio.SetStateAsync('Off').GetAwaiter().GetResult() }"],
            capture_output=True, timeout=10,
        )
        print("⚫ Bluetooth disabled")
    except Exception as e:
        os.system("start ms-settings:bluetooth")
        print(f"⚫ Opened Bluetooth settings (auto-toggle failed: {e})")


# ── System control ────────────────────────────────────────────
def system_action(action):
    if action == "SHUTDOWN":
        os.system("shutdown /s /t 1")
    elif action == "RESTART":
        os.system("shutdown /r /t 1")
    elif action == "SLEEP":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif action == "LOCK":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif action == "SCREENSHOT":
        img      = pyautogui.screenshot()
        filename = f"screenshot_{int(time.time())}.png"
        img.save(filename)
        print(f"📸 Screenshot saved: {filename}")


# ── Screen AI wrappers (used by execute_action) ───────────────
def screen_click_element(description):
    """Use vision AI to find and click a UI element on screen."""
    print(f"👁️ Screen AI: Finding and clicking '{description}'...")
    success = find_and_click_element(description)
    if not success:
        print(f"⚠️ Could not find '{description}' on screen")
    return success


def screen_type_in_field(text, field_description=None):
    """Use vision AI to find an input field, click it, and type text."""
    field_desc = field_description or "text input field, search bar, or prompt box"
    print(f"👁️ Screen AI: Finding input field and typing '{text}'...")
    success = find_and_type_in_field(text, field_desc, press_enter=True)
    if not success:
        print("⚠️ Could not find input field on screen")
    return success


# ── WhatsApp messaging ────────────────────────────────────────
def send_whatsapp_message(recipient, message):
    """Open WhatsApp Desktop, search for recipient, and send a message."""
    print(f"📱 WhatsApp: Sending to '{recipient}' → '{message}'")
    try:
        open_application("whatsapp"); time.sleep(3)
        pyautogui.hotkey('ctrl', 'f'); time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a'); time.sleep(0.1)
        if _PYPERCLIP_AVAILABLE:
            import pyperclip
            pyperclip.copy(recipient)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(recipient, interval=0.05)
        time.sleep(1.5)
        pyautogui.press('enter'); time.sleep(1)
        if _PYPERCLIP_AVAILABLE:
            import pyperclip
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(message, interval=0.05)
        time.sleep(0.3)
        pyautogui.press('enter')
        print(f"✅ WhatsApp message sent to {recipient}!")
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")


# ── Google Flow ASMR video automation ─────────────────────────
_FLOW_HOME_URL = "https://labs.google/fx/tools/flow"

_FLOW_IMAGE_PROMPT_TEMPLATE = (
    "Shot in extreme macro perspective, a flawless, crystal-clear, and detail-rich {coloru} natural texture "
    "{object} rests on a wooden cutting board and sunlight casts a warm glow, creating a dramatic shadow. "
    "The camera captures the shimmering highlights and rainbow-like prismatic flares on the surface of the "
    "{object}. A black gloved hand holding a knife is poised above the {object}, with the blade reflecting "
    "light. The overall composition is centered, with the {object} as the focal point, and the background is "
    "softly blurred, emphasizing the subject's vivid colors and textures."
)

_FLOW_VIDEO_PROMPT_TEMPLATE = (
    "Ultra-realistic 8K ASMR video of a human hand slicing a hyper-detailed {object} made of {material} on a wooden cutting board. "
    "The scene shows the dominant hand holding the knife above the object, fingers curled slightly inward, while the non-dominant "
    "hand gently steadies the object with fingertips resting lightly on top or at the side. The knife blade is angled diagonally "
    "with the tip slightly downward, beginning the slice at the front edge and following through toward the back, clearly revealing "
    "textures and interiors as it moves. "
    "The {object} has a smooth {surface_effect} surface with faint etched rind stripes, with a glossy, mirror-like reflective finish, "
    "with subtle glowing veins beneath the surface that emit a steady neon green radiance and intensify at the point of contact. "
    "As the knife cuts slowly and steadily with controlled pressure, a fine glowing fracture line forms instantly and travels smoothly "
    "along the blade edge, accompanied by tiny sparkling glass particles is revealed. Inside, layered neon glass flesh with a bright "
    "luminous core appears, glowing more intensely and softly pulsing once exposed to air. "
    "The slices separate cleanly with a precise, satisfying split, producing a crisp sequence of high-pitched glass scoring, a sharp "
    "clean crack, delicate cascading micro-tinkles, and a smooth crystalline glide followed by a soft resonant ring. The exposed "
    "interior emits a vibrant neon glow, casting sharp refracted light patterns and subtle green reflections across the wooden surface. "
    "Close-up macro shot with shallow depth of field and cinematic lighting to emphasize the glowing fracture line and the knife edge "
    "passing through the glass. The frame remains completely still throughout the entire cut, with no camera movement, no zoom, and "
    "no transition to another frame, maintaining a natural uninterrupted viewing experience. No background distractions, only the "
    "wooden surface in view. No voice, just immersive ASMR audio: fine glass scoring, crisp crack transitions, layered micro-tinkling "
    "shards, smooth slicing resonance, and a lingering high-frequency glass chime that gently fades into silence. "
    "Cinematic improvement: Add ultra-subtle light bloom at the cut line to heighten realism. "
    "Material consistency: Introduce slight internal tension lines before the crack for more believable physics. "
    "ASMR sound enhancement: Include a faint pre-contact micro-scrape plus tension hum just before the blade fully engages, microscopic "
    "crackle textures layered under the main snap, and a brief shimmering resonance after separation for a premium ASMR finish."
)

# Hardcoded 11-step coordinate plan for Flow automation
_FLOW_11_STEPS = {
    1: "open/create project",   2: "select model picker",
    3: "select image mode",     4: "focus image prompt input",
    5: "submit image generation",
    6: "select generated image result",
    7: "select model picker again",
    8: "select video mode",     9: "submit video generation",
    10: "select generated video result",
    11: "download video",
}

_FLOW_11_CLICK_PLAN = [
    {"step": 1,  "button": "left", "x": 1430, "y": 1534},
    {"step": 2,  "button": "left", "x": 1782, "y": 1674},
    {"step": 3,  "button": "left", "x": 1540, "y": 1237},
    {"step": 4,  "button": "left", "x": 1024, "y": 1599},
    {"step": 5,  "button": "left", "x": 1992, "y": 1676},
    {"step": 6,  "button": "left", "x": 901,  "y": 1675},
    {"step": 7,  "button": "left", "x": 918,  "y": 564},
    {"step": 8,  "button": "left", "x": 1024, "y": 1599},
    {"step": 9,  "button": "left", "x": 1992, "y": 1676},
    {"step": 10, "button": "left", "x": 390,  "y": 701},
    {"step": 11, "button": "left", "x": 2374, "y": 229},
]


def _flow_wait(condition, timeout, interval=4, stable_checks=2):
    print(f"⏳ Waiting for: {condition}")
    ok = wait_for_visual_condition(condition, timeout=timeout,
                                   interval=interval, stable_checks=stable_checks)
    print("✅ Condition reached" if ok else "⚠️ Condition wait timed out")
    return ok


def _safe_format_flow_template(template, **kwargs):
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def _build_flow_prompts(subject, image_prompt=None, video_prompt=None,
                        color="iridescent", material="glass",
                        surface_effect="crystalline"):
    subject        = (subject or "apple").strip()
    color          = (color or "iridescent").strip()
    material       = (material or "glass").strip()
    surface_effect = (surface_effect or "crystalline").strip()
    img = (image_prompt.strip() if image_prompt
           else _safe_format_flow_template(
               _FLOW_IMAGE_PROMPT_TEMPLATE,
               subject=subject, object=subject, coloru=color, color=color))
    vid = (video_prompt.strip() if video_prompt
           else _safe_format_flow_template(
               _FLOW_VIDEO_PROMPT_TEMPLATE,
               subject=subject, object=subject,
               material=material, surface_effect=surface_effect))
    return subject, img, vid


def _parse_flow_payload(target=None, value=None):
    """Support value as dict or JSON string for Gemini compatibility."""
    payload = {}
    if isinstance(value, dict):
        payload = value
    elif isinstance(value, str):
        raw = value.strip()
        if raw.startswith("{") and raw.endswith("}"):
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"subject": raw}
        elif raw:
            payload = {"subject": raw}
    return {
        "subject":       payload.get("subject") or target or "apple",
        "color":         payload.get("color") or payload.get("colour") or "iridescent",
        "material":      payload.get("material") or "glass",
        "surface_effect": payload.get("surface_effect") or payload.get("surface") or "crystalline",
        "image_prompt":  payload.get("image_prompt"),
        "video_prompt":  payload.get("video_prompt"),
        "image_timeout": int(payload.get("image_timeout", 120)),
        "video_timeout": int(payload.get("video_timeout", 240)),
    }


def _click_for_step(step_no, click):
    button = click.get("button", "left")
    if button not in ["left", "right", "middle"]:
        button = "left"
    x, y = click["x"], click["y"]
    _native_click_at(x, y, button=button)
    print(f"🖱️ Step {step_no}/11 ({_FLOW_11_STEPS.get(step_no, 'step')}) -> {button} click at ({x}, {y})")


def _smart_wait_after_step(step_no):
    """Wait for UI to stabilize after each step using vision checks."""
    conditions = {
        1:  "Flow project editor is visible with bottom prompt bar and page is loaded.",
        2:  "Model/type menu is opened and options are visible.",
        3:  "Image mode appears selected and prompt input is ready.",
        4:  "Prompt input field is focused and ready to type.",
        6:  "Generated image is visible/selectable and UI is responsive.",
        7:  "Model/type menu is opened again and options are visible.",
        8:  "Video mode appears selected and prompt input is ready.",
        10: "Generated video result is visible and UI is responsive.",
        11: "Download action is visible or file download is triggered.",
    }
    cond = conditions.get(step_no)
    if not cond:
        return
    ok = _flow_wait(cond, timeout=14, interval=2, stable_checks=1)
    if not ok:
        time.sleep(1.2)


def _run_flow_coded_steps(image_prompt, video_prompt,
                           image_timeout=120, video_timeout=240):
    """Execute the hardcoded 11-step Flow automation plan."""
    if not _PYPERCLIP_AVAILABLE:
        print("❌ pyperclip required for Flow automation. Run: pip install pyperclip")
        return False

    import pyperclip
    print("🎯 Running coded 11-step flow from in-code coordinates")
    print("🧭 Active coordinate map (step -> x,y):")
    for item in _FLOW_11_CLICK_PLAN:
        print(f"   {item['step']}: ({item['x']}, {item['y']})")

    for item in _FLOW_11_CLICK_PLAN:
        step_no = int(item["step"])
        _click_for_step(step_no, item)

        if step_no not in [5, 9]:
            _smart_wait_after_step(step_no)

        if step_no == 4:
            pyperclip.copy(image_prompt)
            pyautogui.hotkey("ctrl", "v")
            print("⌨️ Image prompt pasted after step 4")
            time.sleep(0.35)
        elif step_no == 5:
            image_ready = _flow_wait(
                "A generated image result is visible on canvas and no active loading "
                "spinner/progress for image generation is visible.",
                timeout=image_timeout, interval=4, stable_checks=2,
            )
            if not image_ready:
                print("⚠️ Image wait timed out during step 5")
        elif step_no == 8:
            pyperclip.copy(video_prompt)
            pyautogui.hotkey("ctrl", "v")
            print("⌨️ Video prompt pasted after step 8")
            time.sleep(0.35)
        elif step_no == 9:
            video_ready = _flow_wait(
                "A generated video result is visible and playable, with no active "
                "generation spinner/progress.",
                timeout=video_timeout, interval=5, stable_checks=2,
            )
            if not video_ready:
                print("⚠️ Video wait timed out during step 9")

    print("✅ Coded 11-step flow completed")
    return True


def run_flow_image_to_video(subject, image_prompt=None, video_prompt=None,
                             image_timeout=120, video_timeout=240,
                             color="iridescent", material="glass",
                             surface_effect="crystalline"):
    """
    Full Google Flow pipeline:
    Open Flow → create project → generate image → generate video → download.
    """
    subject, image_prompt, video_prompt = _build_flow_prompts(
        subject, image_prompt, video_prompt,
        color=color, material=material, surface_effect=surface_effect,
    )
    print("=" * 70)
    print(f"🎬 Flow automation started for subject: {subject}")
    print(f"🖼️ Image prompt: {image_prompt}")
    print(f"🎥 Video prompt: {video_prompt}")
    print("=" * 70)

    open_url(_FLOW_HOME_URL)
    time.sleep(2.5)
    print("📂 Using in-code 11-step coordinate plan")
    try:
        ok = _run_flow_coded_steps(image_prompt=image_prompt, video_prompt=video_prompt,
                                    image_timeout=image_timeout, video_timeout=video_timeout)
        if ok:
            print("🏁 Flow automation finished")
            return True
        print("❌ Coded click flow execution did not complete")
        return False
    except Exception as e:
        print(f"❌ Flow automation failed: {e}")
        return False


# ── Single action executor ─────────────────────────────────────
def execute_action(action, target=None, value=None):
    """Execute a single action. Used by both the intent classifier and Gemini brain."""
    print(f"⚙️ Executing: {action} | Target: {target} | Value: {value}")
    try:
        # Volume
        if action == "VOLUME_UP":          change_volume(10)
        elif action == "VOLUME_DOWN":      change_volume(-10)
        elif action == "SET_VOLUME":
            if value is not None:          set_volume(value)
        elif action == "MUTE":             mute_volume()
        elif action == "UNMUTE":           unmute_volume()

        # Brightness
        elif action == "BRIGHTNESS_UP":    change_brightness(10)
        elif action == "BRIGHTNESS_DOWN":  change_brightness(-10)
        elif action == "SET_BRIGHTNESS":
            if value is not None:          set_brightness(int(value))

        # Connectivity
        elif action == "WIFI_ON":          wifi_on()
        elif action == "WIFI_OFF":         wifi_off()
        elif action == "BLUETOOTH_ON":     bluetooth_on()
        elif action == "BLUETOOTH_OFF":    bluetooth_off()

        # Apps
        elif action == "OPEN_APP":
            if target:                     open_application(target)
        elif action == "CLOSE_APP":
            if target:                     close_application(target)

        # Web
        elif action == "SEARCH_WEB":
            query = value or target
            if query:                      search_web(query)
        elif action == "OPEN_URL":
            url = value or target
            if url:                        open_url(str(url))

        # Input
        elif action == "TYPE_TEXT":
            if value:                      type_text(str(value))
        elif action == "PRESS_KEYBOARD_KEY":
            key = value or target
            if key:                        press_key(str(key))
        elif action == "CLICK_MOUSE":      click_mouse()
        elif action == "MOVE_MOUSE":
            if target and value:           move_mouse(int(target), int(value))

        # Virtual desktop
        elif action == "SWITCH_DESKTOP_LEFT":  switch_desktop_left()
        elif action == "SWITCH_DESKTOP_RIGHT": switch_desktop_right()

        # Media
        elif action == "PLAY_MEDIA":       play_media()
        elif action == "PAUSE_MEDIA":      pause_media()
        elif action == "STOP_MEDIA":       stop_media()
        elif action == "NEXT_TRACK":       next_track()
        elif action == "PREV_TRACK":       prev_track()

        # Screen AI
        elif action == "SCREEN_CLICK_ELEMENT":
            desc = value or target or "button"
            screen_click_element(str(desc))
        elif action == "SCREEN_TYPE_IN_FIELD":
            text_to_type = str(value) if value else ""
            field_desc   = str(target) if target else None
            if text_to_type:
                screen_type_in_field(text_to_type, field_desc)
            else:
                print("⚠️ SCREEN_TYPE_IN_FIELD needs value (text to type)")

        # Google Flow ASMR
        elif action == "FLOW_ASMR_VIDEO":
            payload = _parse_flow_payload(target=target, value=value)
            run_flow_image_to_video(
                subject=payload["subject"],
                image_prompt=payload["image_prompt"],
                video_prompt=payload["video_prompt"],
                image_timeout=payload["image_timeout"],
                video_timeout=payload["video_timeout"],
                color=payload["color"],
                material=payload["material"],
                surface_effect=payload["surface_effect"],
            )

        # WhatsApp
        elif action == "SEND_WHATSAPP":
            if target and value:
                send_whatsapp_message(target, str(value))
            else:
                print("⚠️ SEND_WHATSAPP needs both target (recipient) and value (message)")

        # System
        elif action in ["SHUTDOWN", "RESTART", "SLEEP", "LOCK", "SCREENSHOT"]:
            system_action(action)

        elif action == "WAIT":
            time.sleep(float(value) if value else 1.0)

        # Talk-only intents (Gemini handles the speech; no PC action needed)
        elif action in ["GREETING", "HOW_ARE_YOU", "THANKS", "WHO_ARE_YOU"]:
            pass

        else:
            print(f"⚠️ Unknown action: {action}")

    except Exception as e:
        print(f"❌ Error executing {action}: {e}")


def execute_steps(steps):
    """Execute a list of action steps returned by the Gemini brain."""
    if not steps:
        return
    for step in steps:
        execute_action(
            action=step.get("action"),
            target=step.get("target"),
            value=step.get("value"),
        )


# ══════════════════════════════════════════════════════════════
# SECTION 7 — INTENT CLASSIFIER (offline, Hindi/English/Hinglish)
# ══════════════════════════════════════════════════════════════

# Pre-written Hindi responses with multiple variations for natural feel
_RESPONSES = {
    "VOLUME_UP": [
        "वॉल्यूम बढ़ा दिया बाबू!", "लो जी, आवाज़ बढ़ा दी।",
        "वॉल्यूम ऊपर कर दिया, अब सुनाई दे रहा है ना?",
        "आवाज़ तेज़ कर दी, और बढ़ाऊँ?", "बस ये लो, वॉल्यूम बढ़ गया!",
        "हाँ जी, आवाज़ बढ़ा रही हूँ।", "ओके, वॉल्यूम अप कर दिया!",
    ],
    "VOLUME_DOWN": [
        "वॉल्यूम कम कर दिया।", "आवाज़ थोड़ी कम कर दी।",
        "लो जी, धीमा कर दिया।", "वॉल्यूम डाउन कर दिया, ठीक है ना?",
        "हाँ, आवाज़ कम कर रही हूँ।", "ओके, वॉल्यूम नीचे किया!",
    ],
    "SET_VOLUME": [
        "वॉल्यूम {value} परसेंट पे सेट कर दिया!",
        "लो जी, आवाज़ {value}% कर दी।",
        "हाँ बोलो, वॉल्यूम {value} पर लगा दिया।",
        "ओके डन, वॉल्यूम अब {value}% है।",
        "बस जी, {value} परसेंट पे सेट है अब।",
        "वॉल्यूम {value}% किया, और कुछ?",
    ],
    "MUTE": [
        "म्यूट कर दिया, शांति!", "चुप कर दिया सब कुछ।",
        "ओके, आवाज़ बंद कर दी।", "म्यूट हो गया, अब सन्नाटा है।",
        "लो जी, साउंड ऑफ कर दिया।", "हाँ बाबू, म्यूट कर दिया।",
    ],
    "UNMUTE": [
        "अनम्यूट कर दिया!", "आवाज़ वापस आ गई!",
        "लो जी, साउंड ऑन कर दिया।", "म्यूट हटा दिया, अब सुनो।",
        "ओके, आवाज़ चालू कर दी।",
    ],
    "BRIGHTNESS_UP": [
        "ब्राइटनेस बढ़ा दी!", "स्क्रीन और तेज़ कर दी।",
        "लो जी, रोशनी बढ़ा दी।", "ब्राइटनेस ऊपर कर दी, दिख रहा है ना?",
        "हाँ, और चमकदार कर दी स्क्रीन।",
    ],
    "BRIGHTNESS_DOWN": [
        "ब्राइटनेस कम कर दी।", "स्क्रीन थोड़ी डिम कर दी।",
        "लो जी, रोशनी कम कर दी।", "ब्राइटनेस डाउन कर दी, आँखों को आराम।",
        "हाँ, धीमी कर दी स्क्रीन।",
    ],
    "SET_BRIGHTNESS": [
        "ब्राइटनेस {value}% कर दी!",
        "लो जी, स्क्रीन {value} परसेंट पे सेट है।",
        "ब्राइटनेस {value}% पर लगा दी।",
        "ओके, {value}% ब्राइटनेस सेट है अब।",
    ],
    "WIFI_ON": [
        "वाईफाई ऑन कर दिया!", "लो जी, वाईफाई चालू है अब।",
        "वाईफाई कनेक्ट कर रही हूँ।", "हाँ बाबू, वाईफाई ऑन कर दिया।",
        "ओके, इंटरनेट चालू कर दिया।",
    ],
    "WIFI_OFF": [
        "वाईफाई ऑफ कर दिया।", "इंटरनेट बंद कर दिया।",
        "लो जी, वाईफाई डिसकनेक्ट कर दिया।", "ओके, वाईफाई बंद है अब।",
        "हाँ, वाईफाई ऑफ कर रही हूँ।",
    ],
    "BLUETOOTH_ON": [
        "ब्लूटूथ ऑन कर दिया!", "लो जी, ब्लूटूथ चालू है।",
        "हाँ बाबू, ब्लूटूथ ऑन कर दिया।", "ब्लूटूथ कनेक्शन चालू कर दिया।",
    ],
    "BLUETOOTH_OFF": [
        "ब्लूटूथ ऑफ कर दिया।", "लो जी, ब्लूटूथ बंद कर दिया।",
        "ओके, ब्लूटूथ डिसकनेक्ट कर दिया।", "हाँ, ब्लूटूथ बंद है अब।",
    ],
    "SCREENSHOT": [
        "स्क्रीनशॉट ले लिया!", "लो जी, फोटो खींच ली स्क्रीन की।",
        "स्क्रीनशॉट सेव हो गया!", "हाँ बाबू, स्क्रीन कैप्चर कर लिया।",
        "ओके, स्क्रीनशॉट ले लिया है।",
    ],
    "SHUTDOWN": [
        "ओके, सिस्टम बंद कर रही हूँ। बाय बाय!",
        "शटडाउन कर रही हूँ, मिलते हैं फिर!",
        "कंप्यूटर बंद हो रहा है, टेक केयर!",
    ],
    "RESTART": [
        "रीस्टार्ट कर रही हूँ, थोड़ी देर रुको।",
        "सिस्टम रीस्टार्ट हो रहा है!",
        "ओके, रीबूट कर रही हूँ।",
    ],
    "SLEEP": [
        "कंप्यूटर को सुला रही हूँ, गुड नाइट!",
        "स्लीप मोड में डाल रही हूँ।",
        "ओके, सिस्टम सो रहा है अब।",
    ],
    "LOCK": [
        "स्क्रीन लॉक कर दी!", "लो जी, पीसी लॉक है अब।",
        "लॉक कर दिया, सेफ है अब।", "ओके, स्क्रीन लॉक कर दी।",
    ],
    "OPEN_APP": [
        "{target} खोल रही हूँ!", "लो जी, {target} ओपन कर रही हूँ।",
        "हाँ बाबू, {target} चालू कर रही हूँ।",
        "ओके, {target} खोलती हूँ।",
        "{target} स्टार्ट कर रही हूँ, रुको ज़रा।",
    ],
    "CLOSE_APP": [
        "{target} बंद कर दिया!", "लो जी, {target} क्लोज़ कर दिया।",
        "ओके, {target} बंद कर रही हूँ।", "{target} बंद है अब।",
    ],
    "SEARCH_WEB": [
        "{value} सर्च कर रही हूँ!", "लो जी, गूगल पे {value} ढूँढ रही हूँ।",
        "ओके, {value} सर्च करती हूँ।",
        "हाँ, {value} खोज रही हूँ इंटरनेट पे।",
    ],
    "SWITCH_DESKTOP_LEFT": [
        "लेफ्ट डेस्कटॉप पे जा रही हूँ!", "ओके, बाएं डेस्कटॉप पे स्विच कर रही हूँ।",
        "हाँ, दूसरे डेस्कटॉप पे जा रही हूँ।", "लेफ्ट साइड का डेस्कटॉप खोल रही हूँ।",
    ],
    "SWITCH_DESKTOP_RIGHT": [
        "राइट डेस्कटॉप पे वापस आ रही हूँ!",
        "ओके, दाएं डेस्कटॉप पे स्विच कर रही हूँ।",
        "वापस आ गई मैन डेस्कटॉप पे!", "राइट साइड का डेस्कटॉप खोल रही हूँ।",
    ],
    "PLAY_MEDIA": [
        "गाना चालू कर दिया!", "लो जी, म्यूज़िक प्ले कर रही हूँ।",
        "ओके, सॉन्ग बजा रही हूँ!", "हाँ, गाना शुरू कर दिया।",
        "म्यूज़िक प्ले कर दिया!",
    ],
    "PAUSE_MEDIA": [
        "गाना रोक दिया!", "लो जी, म्यूज़िक पॉज़ कर दिया।",
        "ओके, सॉन्ग रुक गया।", "हाँ, गाना रोक दिया अभी।",
    ],
    "STOP_MEDIA": [
        "म्यूज़िक बंद कर दिया!", "गाना स्टॉप कर दिया।", "ओके, म्यूज़िक बंद है अब।",
    ],
    "NEXT_TRACK": [
        "अगला गाना लगा दिया!", "नेक्स्ट ट्रैक पे जा रही हूँ।", "ओके, अगला सॉन्ग चालू!",
    ],
    "PREV_TRACK": [
        "पिछला गाना लगा दिया!", "प्रीवियस ट्रैक पे जा रही हूँ।", "ओके, पहले वाला सॉन्ग!",
    ],
}


def _p(patterns):
    """Compile a list of regex patterns (case-insensitive)."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _clean_target(text):
    """Strip common conversational filler words from extracted targets."""
    if not text:
        return text
    fillers = [r'\bplease\b', r'\bpls\b', r'\bplz\b', r'\bkholdo\b',
               r'\bkhol\s*do\b', r'\bkar\s*do\b', r'\byar\b', r'\byaar\b',
               r'\bbro\b', r'\bbhai\b', r'\bbabu\b', r'\bjaldi\b']
    clean = text
    for f in fillers:
        clean = re.sub(f, '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[!.,]+$', '', clean)
    return clean.strip()


# ── Extractor helpers ──────────────────────────────────────────
def _extract_volume(text):
    m = re.search(r'(\d+)\s*(%|percent|परसेंट)?', text)
    return None, int(m.group(1)) if m else 50

def _extract_brightness(text):
    m = re.search(r'(\d+)\s*(%|percent|परसेंट)?', text)
    return None, int(m.group(1)) if m else 50

def _extract_app_open(text):
    m1 = re.search(r'\b(?:open|launch|start|khol|chalao|chalu\s*kar|खोल|चालू\s*कर|ओपन|लॉन्च|स्टार्ट)\s+(.+)', text, re.IGNORECASE)
    if m1: return _clean_target(m1.group(1)), None
    m2 = re.search(r'(.+?)\s+(?:open|khol|kholdo|khol\s*do|chalao|chalu|खोल|खोल\s*दो|चालू)', text, re.IGNORECASE)
    if m2: return _clean_target(m2.group(1)), None
    return _clean_target(text), None

def _extract_app_close(text):
    m1 = re.search(r'\b(?:close|exit|quit|kill|band\s*kar|hatao|बंद\s*कर|हटा|क्लोज़?)\s+(.+)', text, re.IGNORECASE)
    if m1: return _clean_target(m1.group(1)), None
    m2 = re.search(r'(.+?)\s+(?:band|close|बंद|hatao|hata\s*do|हटा|हटा\s*दो)', text, re.IGNORECASE)
    if m2: return _clean_target(m2.group(1)), None
    return _clean_target(text), None

def _extract_search(text):
    m = re.search(r'\b(?:search|google|find|dhoond|dhundh|khoj|talaash|ढूँढ|खोज|सर्च|गूगल|तलाश)\s+(?:for|pe|par|पर|पे)?\s*(.+)', text, re.IGNORECASE)
    if m: return None, _clean_target(m.group(1))
    return None, _clean_target(text)


# ── Intent pattern table ───────────────────────────────────────
_INTENTS = [
    # Volume Up
    (_p([
        r"\b(volume|vol|sound|awaz|awaaz|aawaz|आवाज़?|वॉल्यूम|साउंड)\b.*(up|increase|badha|badhao|upar|uper|tez|tej|zyada|jyada|बढ़ा|ऊपर|तेज़?|ज़्यादा)",
        r"\b(badha|badhao|tez|tej)\b.*(volume|vol|sound|awaz|awaaz|आवाज़?|वॉल्यूम)",
        r"\b(volume|vol)\s*(up|badha|badhao)\b",
        r"\b(awaaz|awaz|aawaz)\s*(badha|badhao|tez|zyada)\b",
        r"\blouder\b", r"\bturn\s*(it\s*)?up\b",
        r"\braise\s*(the\s*)?(volume|sound)\b",
        r"\bआवाज़?\s*(बढ़ा|तेज़?)\b", r"\bवॉल्यूम\s*(बढ़ा|अप|ऊपर)\b",
    ]), "VOLUME_UP", None),

    # Volume Down
    (_p([
        r"\b(volume|vol|sound|awaz|awaaz|aawaz|आवाज़?|वॉल्यूम|साउंड)\b.*(down|decrease|kam|dhima|dhime|niche|neeche|कम|नीचे|धीमा|धीमे)",
        r"\b(kam|dhima|dhime)\b.*(volume|vol|sound|awaz|awaaz|आवाज़?|वॉल्यूम)",
        r"\b(volume|vol)\s*(down|kam|dhima)\b",
        r"\b(awaaz|awaz|aawaz)\s*(kam|dhima|dhime|halka)\b",
        r"\bquieter\b", r"\bturn\s*(it\s*)?down\b",
        r"\blower\s*(the\s*)?(volume|sound)\b",
        r"\bआवाज़?\s*(कम|धीम[ाेी])\b", r"\bवॉल्यूम\s*(कम|डाउन|नीचे)\b",
    ]), "VOLUME_DOWN", None),

    # Set Volume
    (_p([
        r"\b(volume|vol|sound|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*\b(\d+)\s*(%|percent|परसेंट)?\b",
        r"\b(set|change|kar|rakh|rakho|सेट|रख)\b.*(volume|vol|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*\b(\d+)",
        r"\b(\d+)\s*(%|percent|परसेंट)?\s*(volume|vol|awaz|awaaz|आवाज़?|वॉल्यूम)\b",
        r"\bवॉल्यूम\s*(\d+)\b", r"\bआवाज़?\s*(\d+)\b", r"\b(volume|vol)\s+(\d+)\b",
    ]), "SET_VOLUME", _extract_volume),

    # Mute
    (_p([
        r"\b(mute|silent|shant|chup|शांत|म्यूट|चुप|बंद\s*कर.*आवाज़?)\b",
        r"\b(sound|volume|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*(off|band|बंद|mute)\b",
        r"\b(band|बंद)\b.*(sound|awaz|awaaz|आवाज़?|volume)\b",
        r"\bsilence\b", r"\bshut\s*up\b", r"\bआवाज़?\s*(बंद|ऑफ)\b",
    ]), "MUTE", None),

    # Unmute
    (_p([
        r"\b(unmute|अनम्यूट)\b",
        r"\b(sound|volume|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*(on|chalu|shuru|चालू)\b",
        r"\b(chalu|shuru|चालू)\b.*(sound|awaz|awaaz|आवाज़?|volume)\b",
        r"\bआवाज़?\s*(चालू|ऑन)\b",
    ]), "UNMUTE", None),

    # Brightness Up
    (_p([
        r"\b(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|चमक|रोशनी|ब्राइटनेस)\b.*(up|increase|badha|badhao|tez|बढ़ा|तेज़?|ज़्यादा|zyada)",
        r"\b(badha|badhao|tez)\b.*(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|रोशनी|ब्राइटनेस)",
        r"\bbrighter\b", r"\bरोशनी\s*(बढ़ा|तेज़?)\b", r"\bब्राइटनेस\s*(बढ़ा|अप|ऊपर)\b",
    ]), "BRIGHTNESS_UP", None),

    # Brightness Down
    (_p([
        r"\b(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|चमक|रोशनी|ब्राइटनेस)\b.*(down|decrease|kam|dhima|कम|धीमा|नीचे)",
        r"\b(kam|dhima)\b.*(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|रोशनी|ब्राइटनेस)",
        r"\bdimmer?\b", r"\bdim\s*(the\s*)?(screen|light)\b",
        r"\bरोशनी\s*(कम|धीमी)\b", r"\bब्राइटनेस\s*(कम|डाउन)\b",
    ]), "BRIGHTNESS_DOWN", None),

    # Set Brightness
    (_p([
        r"\b(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|ब्राइटनेस|रोशनी)\b.*\b(\d+)\s*(%|percent|परसेंट)?\b",
        r"\b(set|change|kar|rakh)\b.*(brightness|bright|brighness|brightnes|brigthness|roshni|ब्राइटनेस|रोशनी)\b.*\b(\d+)",
        r"\b(\d+)\s*(%|percent)?\s*(brightness|bright|brighness|brightnes|brigthness)\b",
        r"\bब्राइटनेस\s*(\d+)\b",
    ]), "SET_BRIGHTNESS", _extract_brightness),

    # WiFi On
    (_p([
        r"\b(wifi|wi-fi|वाईफाई|वाई\s*फाई|internet|इंटरनेट)\b.*(on|chalu|enable|start|connect|jodo|चालू|ऑन|कनेक्ट)",
        r"\b(chalu|on|enable|start|connect|चालू|ऑन)\b.*(wifi|wi-fi|वाईफाई|internet|इंटरनेट)\b",
        r"\bturn\s*on\s*(the\s*)?(wifi|wi-fi|internet)\b",
        r"\b(wifi|wi-fi)\s*(on|chalu|चालू)\b",
        r"\bवाईफाई\s*(चालू|ऑन|कनेक्ट)\b", r"\bइंटरनेट\s*(चालू|ऑन)\b",
        r"\bnet\s*(on|chalu|chalao)\b",
    ]), "WIFI_ON", None),

    # WiFi Off
    (_p([
        r"\b(wifi|wi-fi|वाईफाई|वाई\s*फाई|internet|इंटरनेट)\b.*(off|band|disable|stop|disconnect|हटा|बंद|ऑफ|डिसकनेक्ट)",
        r"\b(band|off|disable|stop|disconnect|बंद|ऑफ)\b.*(wifi|wi-fi|वाईफाई|internet|इंटरनेट)\b",
        r"\bturn\s*off\s*(the\s*)?(wifi|wi-fi|internet)\b",
        r"\b(wifi|wi-fi)\s*(off|band|बंद)\b",
        r"\bवाईफाई\s*(बंद|ऑफ|डिसकनेक्ट)\b", r"\bइंटरनेट\s*(बंद|ऑफ)\b",
        r"\bnet\s*(off|band|bandh)\b",
    ]), "WIFI_OFF", None),

    # Bluetooth On
    (_p([
        r"\b(bluetooth|bt|ब्लूटूथ|ब्लूटूस)\b.*(on|chalu|enable|start|connect|चालू|ऑन|कनेक्ट)",
        r"\b(chalu|on|enable|start|चालू|ऑन)\b.*(bluetooth|bt|ब्लूटूथ)\b",
        r"\bturn\s*on\s*(the\s*)?(bluetooth|bt)\b",
        r"\b(bluetooth|bt)\s*(on|chalu|चालू)\b", r"\bब्लूटूथ\s*(चालू|ऑन)\b",
    ]), "BLUETOOTH_ON", None),

    # Bluetooth Off
    (_p([
        r"\b(bluetooth|bt|ब्लूटूथ|ब्लूटूस)\b.*(off|band|disable|stop|disconnect|बंद|ऑफ)",
        r"\b(band|off|disable|stop|disconnect|बंद|ऑफ)\b.*(bluetooth|bt|ब्लूटूथ)\b",
        r"\bturn\s*off\s*(the\s*)?(bluetooth|bt)\b",
        r"\b(bluetooth|bt)\s*(off|band|बंद)\b", r"\bब्लूटूथ\s*(बंद|ऑफ)\b",
    ]), "BLUETOOTH_OFF", None),

    # Screenshot
    (_p([
        r"\b(screenshot|screen\s*shot|ss|स्क्रीनशॉट|स्क्रीन\s*शॉट)\b",
        r"\b(capture|कैप्चर)\s*(screen|स्क्रीन)\b",
        r"\b(photo|फोटो)\s*(screen|स्क्रीन|le|lo|ले|लो)\b",
        r"\bscreen\s*(capture|photo|pic)\b", r"\btak\s*a?\s*(screenshot|ss|pic)\b",
        r"\bस्क्रीन\s*(की\s*)?(फोटो|तस्वीर)\b",
    ]), "SCREENSHOT", None),

    # Shutdown
    (_p([
        r"\b(shutdown|shut\s*down|power\s*off|शटडाउन|बंद\s*कर\s*(दो|दे|do)?(\s*कंप्यूटर)?)\b",
        r"\b(computer|pc|system|कंप्यूटर|पीसी|सिस्टम)\b.*(band|off|shutdown|बंद)\b",
        r"\b(band|बंद)\b.*(computer|pc|system|कंप्यूटर|पीसी)\b",
        r"\bpower\s*off\b", r"\bपावर\s*ऑफ\b",
    ]), "SHUTDOWN", None),

    # Restart
    (_p([
        r"\b(restart|reboot|रीस्टार्ट|रीबूट)\b",
        r"\b(computer|pc|system|कंप्यूटर|पीसी)\b.*(restart|reboot|रीस्टार्ट)\b",
        r"\bdubara\s*chalu\b", r"\bदुबारा\s*चालू\b",
    ]), "RESTART", None),

    # Sleep
    (_p([
        r"\b(sleep|hibernate|sone\s*do|sula\s*do|स्लीप|सोने\s*दो|सुला\s*दो)\b",
        r"\b(computer|pc|system|कंप्यूटर|पीसी)\b.*(sleep|sone|sula|स्लीप|सो)\b",
        r"\bhibernate\b",
    ]), "SLEEP", None),

    # Lock
    (_p([
        r"\b(lock|screen\s*lock|लॉक)\b",
        r"\b(computer|pc|screen|स्क्रीन|कंप्यूटर|पीसी)\b.*(lock|लॉक)\b",
        r"\b(lock|लॉक)\b.*(computer|pc|screen|स्क्रीन|कंप्यूटर)\b",
        r"\bस्क्रीन\s*लॉक\b",
    ]), "LOCK", None),

    # Switch Desktop Left
    (_p([
        r"\b(left|baye[mn]?|बाए[ंम]?|लेफ्ट)\s+(desktop|screen|डेस्कटॉप|स्क्रीन)",
        r"\b(desktop|डेस्कटॉप)\s+(left|baye[mn]?|बाए[ंम]?|लेफ्ट)",
        r"\b(left|baye[mn]?|बाए[ंम]?|लेफ्ट)\b.*(ja|jao|switch|chale?\s*ja|जा|जाओ|स्विच)",
        r"\bleft\s*desktop\s*(mai|me|mein|में|pe|par|पे|पर)?\s*(ja|jao|switch|जा|जाओ)?\\b",
        r"\bdoosre?\s*desktop\b", r"\bdusre?\s*desktop\b",
    ]), "SWITCH_DESKTOP_LEFT", None),

    # Switch Desktop Right
    (_p([
        r"\b(right|daye[mn]?|दाए[ंम]?|राइट)\s+(desktop|screen|डेस्कटॉप|स्क्रीन)",
        r"\b(desktop|डेस्कटॉप)\s+(right|daye[mn]?|दाए[ंम]?|राइट)",
        r"\b(right|daye[mn]?|दाए[ंम]?|राइट)\b.*(ja|jao|switch|chale?\s*ja|जा|जाओ|स्विच)",
        r"\b(wapas|wapis|vapas|वापस|back)\s*(aa|aao|आ|आओ|ja|jao)\b",
        r"\b(main|original|pehle?\s*wala?)\s*(desktop|डेस्कटॉप)",
    ]), "SWITCH_DESKTOP_RIGHT", None),

    # Play Media
    (_p([
        r"\b(play|baja|bajao|chala|chalao|resume|प्ले|बजा|बजाओ|चला|चलाओ)\s*(song|music|gaana|gana|media|track|सॉन्ग|गाना|म्यूज़िक|म्यूजिक)?\b",
        r"\b(song|music|gaana|gana|सॉन्ग|गाना|म्यूज़िक|म्यूजिक)\s*(play|baja|bajao|chala|chalao|shuru|प्ले|बजा|चला|चलाओ|शुरू)\b",
        r"\b(song|gaana|gana|music|गाना|सॉन्ग|म्यूज़िक)\s*(kar|karo|kr|करो?)\b",
        r"\bplay\s*kr\b", r"\bgaana\s*(baja|chala|laga|शुरू)\b",
        r"\bmusic\s*(on|chalu|start|play)\b",
    ]), "PLAY_MEDIA", None),

    # Pause Media
    (_p([
        r"\b(pause|rok|roko|ruk|ruko|tham|thaam|पॉज़?|रोक|रोको|रुक|रुको|थाम)\s*(song|music|gaana|gana|media|सॉन्ग|गाना|म्यूज़िक)?\b",
        r"\b(song|music|gaana|gana|सॉन्ग|गाना|म्यूज़िक)\s*(pause|rok|roko|band|पॉज़?|रोक|रोको|बंद)\b",
        r"\b(gaana|gana|song|music|गाना)\s*(rok|roko|band\s*kar|रोक|बंद)\b",
    ]), "PAUSE_MEDIA", None),

    # Stop Media
    (_p([
        r"\b(stop|band)\s*(song|music|gaana|gana|media|सॉन्ग|गाना|म्यूज़िक)\b",
        r"\b(song|music|gaana|gana|सॉन्ग|गाना|म्यूज़िक)\s*(stop|band|बंद|स्टॉप)\s*(kar|karo|kr|करो?)?\b",
        r"\bmusic\s*(off|band|stop)\b",
    ]), "STOP_MEDIA", None),

    # Next Track
    (_p([
        r"\b(next|agla|अगला|नेक्स्ट)\s*(song|track|gaana|gana|सॉन्ग|गाना|ट्रैक)?\b",
        r"\b(song|gaana|gana|track|सॉन्ग|गाना)\s*(skip|next|agla|अगला|नेक्स्ट|स्किप)\b",
        r"\bskip\s*(song|track|gaana)?\b",
    ]), "NEXT_TRACK", None),

    # Previous Track
    (_p([
        r"\b(prev|previous|pichla|पिछला|प्रीवियस)\s*(song|track|gaana|gana|सॉन्ग|गाना|ट्रैक)?\b",
        r"\b(song|gaana|gana|track|सॉन्ग|गाना)\s*(prev|previous|pichla|पिछला)\b",
        r"\bpehle\s*wala\s*(song|gaana|gana)?\b",
    ]), "PREV_TRACK", None),

    # Open App
    (_p([
        r"\b(open|launch|start|run)\s+\w+",
        r"\b(khol|kholdo|khol\s*do|chalao|chalu\s*kar|chalu\s*karo)\s+\w+",
        r"\b(खोल|खोल\s*दो|चालू\s*कर|चालू\s*करो|ओपन|लॉन्च|स्टार्ट)\s+\w+",
        r"\b\w+\s+(open|khol|kholdo|खोल|खोल\s*दो)\b",
        r"\b\w+\s+(chalu|chalao|चालू)\s*(kar|karo|करो?)?\b",
    ]), "OPEN_APP", _extract_app_open),

    # Close App
    (_p([
        r"\b(close|exit|quit|kill|terminate)\s+\w+",
        r"\b(band\s*kar|band\s*karo|hatao|hata\s*do)\s+\w+",
        r"\b(बंद\s*कर|बंद\s*करो|हटा|हटा\s*दो|क्लोज़?)\s+\w+",
        r"\b\w+\s+(band|close|बंद)\s*(kar|karo|करो?)?\b",
    ]), "CLOSE_APP", _extract_app_close),

    # Search Web
    (_p([
        r"\b(search|google|find|look\s*up)\s+.+",
        r"\b(dhoond|dhundh|khoj|talaash)\s+.+",
        r"\b(ढूँढ|खोज|सर्च|गूगल|तलाश)\s+.+",
        r"\b(search|google|सर्च|गूगल)\s+(for|pe|par|पर|पे)?\s*.+",
    ]), "SEARCH_WEB", _extract_search),
]


def classify_intent(text):
    """
    Try to match the user's text to a known intent locally (no API call needed).

    Returns:
        dict: {"action": str, "target": str|None, "value": int|None, "say": str}
        None: if no match → falls through to Gemini
    """
    if not text or not text.strip():
        return None

    text_clean = text.strip()

    for patterns, action, extractor in _INTENTS:
        for pat in patterns:
            if pat.search(text_clean):
                target, value = None, None
                if extractor:
                    target, value = extractor(text_clean)

                say = random.choice(_RESPONSES.get(action, ["ओके, कर दिया!"]))
                say = (say
                       .replace("{value}", str(value) if value is not None else "")
                       .replace("{target}", str(target) if target else ""))
                return {"action": action, "target": target, "value": value, "say": say}

    return None   # Not recognized → send to Gemini


# ══════════════════════════════════════════════════════════════
# SECTION 8 — MEMORY (ChromaDB vector memory)
# ══════════════════════════════════════════════════════════════

_CHROMA_DB_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
_COLLECTION_NAME  = "kypzer_memory"
_EMBEDDING_MODELS = [
    "text-embedding-004",
    "gemini-embedding-001",
    "models/text-embedding-004",
]
_USE_GEMINI_EMBEDDINGS = os.getenv("USE_GEMINI_EMBEDDINGS", "false").strip().lower() in {"1", "true", "yes", "on"}
_MAX_MEMORY_RESULTS = 3

_embed_client   = None
_chroma_client  = None
_mem_collection = None
_active_embedding_model = None


def _get_embed_client():
    global _embed_client
    if _embed_client is None and _CHROMADB_AVAILABLE:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            _embed_client = genai.Client(api_key=api_key)
    return _embed_client


def _get_embedding(text: str):
    if not _USE_GEMINI_EMBEDDINGS:
        return None

    global _active_embedding_model
    client = _get_embed_client()
    if not client:
        return None

    # Reuse last known-good model to avoid repeated 404 model errors.
    candidate_models = [_active_embedding_model] if _active_embedding_model else []
    candidate_models.extend([m for m in _EMBEDDING_MODELS if m != _active_embedding_model])

    for model_name in candidate_models:
        try:
            result = client.models.embed_content(model=model_name, contents=text)
            _active_embedding_model = model_name
            return result.embeddings[0].values
        except Exception as e:
            print(f"⚠️ [Memory] Embedding error with '{model_name}': {e}")

    return None


def _get_mem_collection():
    global _chroma_client, _mem_collection
    if not _CHROMADB_AVAILABLE:
        return None
    if _mem_collection is None:
        try:
            _chroma_client  = chromadb.PersistentClient(path=_CHROMA_DB_PATH)
            _mem_collection = _chroma_client.get_or_create_collection(
                name=_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            count = _mem_collection.count()
            print(f"✅ [Memory] ChromaDB loaded — {count} memories at {_CHROMA_DB_PATH}")
        except Exception as e:
            print(f"❌ [Memory] ChromaDB init failed: {e}")
            _mem_collection = None
    return _mem_collection


def save_conversation(user_msg: str, assistant_reply: str) -> bool:
    """Save a user+assistant exchange to ChromaDB."""
    collection = _get_mem_collection()
    if collection is None:
        return False

    doc_text  = f"User: {user_msg}\nKypzer: {assistant_reply}"
    embedding = _get_embedding(user_msg)
    record_id = f"chat_{int(time.time() * 1000)}"
    metadata  = {"timestamp": str(int(time.time())), "user_msg": user_msg[:500]}

    try:
        if embedding:
            collection.add(documents=[doc_text], embeddings=[embedding],
                           ids=[record_id], metadatas=[metadata])
        else:
            print("⚠️ [Memory] Using fallback embedding")
            collection.add(documents=[doc_text], ids=[record_id], metadatas=[metadata])
        return True
    except Exception as e:
        print(f"❌ [Memory] Save failed: {e}")
        return False


def get_relevant_context(query: str, top_k: int = 1) -> str:
    """
    Search ChromaDB for past conversations relevant to the current query.
    Returns ONLY the most semantically similar memory (strict matching).
    """
    collection = _get_mem_collection()
    if collection is None or collection.count() == 0:
        return ""

    try:
        embedding = _get_embedding(query)
        if embedding is not None:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, collection.count()),
                include=["documents", "distances"],
            )
        else:
            results = collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count()),
                include=["documents", "distances"],
            )
        if not results or not results["documents"] or not results["documents"][0]:
            return ""

        # Cosine distance < 0.5 → semantically similar (working threshold for ChromaDB)
        relevant_docs = [
            doc for doc, dist
            in zip(results["documents"][0], results["distances"][0])
            if dist < 0.5
        ]

        if not relevant_docs:
            return ""

        # Return only the most relevant memory
        context = "--- Past Conversation Context ---\n"
        context += f"\n{relevant_docs[0]}\n"
        context += "\n--- End Context ---"
        return context

    except Exception as e:
        print(f"⚠️ [Memory] Search failed: {e}")
        return ""


def get_memory_count() -> int:
    """Return the number of stored memories."""
    collection = _get_mem_collection()
    return collection.count() if collection else 0


def clear_memory() -> bool:
    """Clear all stored memories."""
    global _mem_collection
    if not _CHROMADB_AVAILABLE:
        return False
    try:
        client = chromadb.PersistentClient(path=_CHROMA_DB_PATH)
        client.delete_collection(_COLLECTION_NAME)
        _mem_collection = None
        print("🗑️ [Memory] All memories cleared.")
        return True
    except Exception as e:
        print(f"❌ [Memory] Clear failed: {e}")
        return False


# Lazy init on import
try:
    _get_mem_collection()
except Exception:
    pass


# ══════════════════════════════════════════════════════════════
# SECTION 9 — BRAIN (Gemini AI processing core)
# ══════════════════════════════════════════════════════════════

# Multiple API keys for automatic rate-limit fallback
_API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
]
_API_KEYS = [k for k in _API_KEYS if k]

_current_key_index = 0
_gemini_client     = None
_GEMINI_MODEL      = "gemini-2.5-flash"

_SYSTEM_PROMPT = """
You are "Kypzer", an intelligent PC gf assistant which controlls pc.
Your goal is to understand the user's intent from their message and output valid JSON commands.
"you should be chill and majak masti type, when something unreconized un ethical or illegal then you should handle with it in majak way" 
You should always try to be helpful and execute the user's commands.


IMPORTANT: 
--Your conversation history with the user may be provided in the prompt context below. 
Use it to remember who the user is, their name, preferences, and past interactions.
--and if you are saying in hindi or  in hinglish , then you should give speaking text in devnagri hindi font and it should be in proper font according to sounds and pronunciation.


JSON format:
{
  "mode": "TALK" or "HYBRID",
  "say": string (what Kypzer speaks back),
  "steps": [
    {
      "action": one of ["VOLUME_UP", "VOLUME_DOWN", "SET_VOLUME", "MUTE", "UNMUTE",
                       "OPEN_APP", "CLOSE_APP", "SEARCH_WEB", "TYPE_TEXT",
                       "SHUTDOWN", "RESTART", "SLEEP", "LOCK",
                       "SCREENSHOT", "SEARCH_IN_APP", "PRESS_KEYBOARD_KEY", "WAIT", "CLICK_MOUSE", "MOVE_MOUSE",
                       "FLOW_ASMR_VIDEO"],
      "target": string or null,
      "value": number/string/null,
      "confidence": number 0.0 to 1.0
    }
  ]
}

Guidelines:
- Return ONLY valid JSON.
- Personality: You are Kypzer. Helpful, smart, slightly witty.
- If user asks to create/generate ASMR cutting image+video in Google Flow, use one step with action "FLOW_ASMR_VIDEO".
- For FLOW_ASMR_VIDEO, set target to subject (e.g. "apple") and value as object:
    {"subject":"apple", "color":"red", "material":"glass", "surface_effect":"mirror-like", "image_prompt":"...", "video_prompt":"...", "image_timeout":120, "video_timeout":240, "use_recorded_clicks":true}
- If unsure or no command detected: {"mode": "TALK", "say": "I didn't quite catch that.", "steps": []}
"""


def _init_gemini_client(key_index=0):
    global _gemini_client, _current_key_index
    if key_index < len(_API_KEYS):
        _current_key_index = key_index
        try:
            _gemini_client = genai.Client(api_key=_API_KEYS[key_index])
            print(f"🔑 Using Gemini Key #{key_index + 1}: "
                  f"{_API_KEYS[key_index][:5]}...{_API_KEYS[key_index][-3:]}")
            return True
        except Exception as e:
            print(f"❌ Failed to init Gemini with Key #{key_index + 1}: {e}")
            return False
    return False


if _API_KEYS:
    _init_gemini_client(0)
else:
    print("❌ No Gemini API Keys found in env.env!")


def process_with_gemini(audio_path=None, text_input=None):
    """
    Send a command to Gemini and return the parsed JSON response.

    Voice flow:  audio → Google STT → Gemini (text-only)
    Text flow:   text  → Gemini (text-only)

    Returns:
        (data_dict, raw_text) on success
        (None, error_string) on failure
    """
    global _gemini_client, _current_key_index

    if not _gemini_client:
        return None, "API Key Missing"

    # Transcribe audio first if provided
    if audio_path and not text_input:
        print("🎙️ Transcribing speech to text (Google online STT)...")
        text_input, err = transcribe_wav_google(audio_path)
        if not text_input:
            return None, err or "Speech transcription failed."

    if not text_input:
        return None, "No input provided"

    print(f"🧠 Processing: {text_input}")
    
    # Fetch relevant past conversations from ChromaDB memory
    past_context = get_relevant_context(text_input)
    if past_context:
        print(f"📚 [Memory] Found relevant context")
    else:
        print(f"📚 [Memory] No relevant past conversation found")
    
    # Build prompt with memory context
    prompt_preamble = _SYSTEM_PROMPT
    if past_context:
        prompt_preamble += "\n\n[Context from past conversations]\n" + past_context
    
    contents = [prompt_preamble, f"User Command: {text_input}"]
    
    # Display the prompt being sent to Gemini
    print("\n" + "="*60)
    print("📤 PROMPT SENT TO GEMINI:")
    print("="*60)
    print(prompt_preamble)
    print(f"\n📝 {contents[1]}")
    print("="*60 + "\n")

    for attempt in range(len(_API_KEYS)):
        try:
            response  = _gemini_client.models.generate_content(
                model=_GEMINI_MODEL, contents=contents)
            raw_text  = response.text
            clean     = raw_text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(clean), raw_text
            except json.JSONDecodeError:
                start = clean.find("{"); end = clean.rfind("}")
                if start != -1 and end != -1:
                    return json.loads(clean[start:end + 1]), raw_text
                return None, raw_text

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"⏳ Rate Limited on Key #{_current_key_index + 1}. Switching...")
                next_key = (_current_key_index + 1) % len(_API_KEYS)
                if _init_gemini_client(next_key):
                    time.sleep(0.5)
                    continue
                print("❌ All API Keys exhausted.")
                return None, error_str
            print(f"❌ Gemini Error: {e}")
            return None, error_str

    return None, "All retries failed."


# ══════════════════════════════════════════════════════════════
# SECTION 10 — MAIN (Entry point)
# ══════════════════════════════════════════════════════════════

# Set to False to enable voice input/output in production
TEXT_ONLY_MODE = True
VOICE_OUTPUT_ENABLED = os.getenv("VOICE_OUTPUT_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def main():
    print("\n" + "=" * 50)
    print("🤖 Kypzer AI (Gemini 2.5 Flash) — Voice PC Assistant")
    if TEXT_ONLY_MODE:
        print("⌨️  Text-only mode is ON (voice input paused).")
        print("⌨️  Type your command and press ENTER.")
    else:
        print("🎤  Press ENTER to start recording (5 seconds).")
    print(f"🔊 Voice output: {'ON' if VOICE_OUTPUT_ENABLED else 'OFF'}")
    print("❌  Type 'exit' to quit.")
    print("=" * 50 + "\n")

    while True:
        try:
            prompt = ("🟢 Enter command (or 'exit'): "
                      if TEXT_ONLY_MODE
                      else "🟢 Press ENTER to speak (or type a command / 'exit'): ")
            user_input = input(prompt).strip()

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Goodbye!")
                if VOICE_OUTPUT_ENABLED:
                    speak("Goodbye! Shutting down systems.")
                break

            # ── Determine transcript ──────────────────────────
            if TEXT_ONLY_MODE:
                if not user_input:
                    continue
                transcript = user_input

            elif user_input:
                # User typed a command instead of speaking
                transcript = user_input

            else:
                # Voice recording path
                audio_file = record_audio()
                if not audio_file or not os.path.exists(audio_file):
                    print("⚠️ Audio recording failed.")
                    continue

                print("📝 Converting speech to text...")
                transcript, stt_err = transcribe_wav_google(audio_file)
                try:
                    os.remove(audio_file)
                except Exception:
                    pass

                if not transcript:
                    print(f"⚠️ STT failed: {stt_err}")
                    continue

            print(f"🗣️ You said: {transcript}")

            # ── Step 1: Try offline intent classifier ──────────
            intent_result = classify_intent(transcript)
            if intent_result:
                say_text = intent_result.get("say", "")
                action   = intent_result.get("action")
                target   = intent_result.get("target")
                value    = intent_result.get("value")

                if say_text:
                    print(f"🤖 Kypzer: {say_text}")
                    if VOICE_OUTPUT_ENABLED:
                        speak(say_text)

                if action:
                    print("\n⚙️ Executing action (offline)...")
                    execute_action(action, target=target, value=value)
                    print("✅ Done.\n")

                # Save to memory
                save_conversation(transcript, say_text or "")
                continue

            # ── Step 2: Fall through to Gemini ─────────────────
            print("🧠 Kypzer is thinking (Gemini)...")
            data, raw_output = process_with_gemini(text_input=transcript)

            if not data:
                print(f"⚠️ Debug Raw: {raw_output}")
                print("⚠️ No valid JSON returned.")
                continue

            mode     = data.get("mode", "TALK")
            say_text = data.get("say", "")
            steps    = data.get("steps", [])

            if not say_text and not steps:
                print("😶 [Ignored - no actionable response]")
                continue

            if say_text:
                print(f"🤖 Kypzer: {say_text}")
                if VOICE_OUTPUT_ENABLED:
                    speak(say_text)

            if steps:
                print("\n⚙️ Executing Actions...")
                execute_steps(steps)
                print("✅ Done.\n")

            # Save to memory
            save_conversation(transcript, say_text or "")

        except KeyboardInterrupt:
            print("\n👋 Force Quit.")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")


if __name__ == "__main__":
    main()
