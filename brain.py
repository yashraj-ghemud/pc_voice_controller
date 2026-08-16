import os
import json
import time
from google import genai
from dotenv import load_dotenv
import stt

# Load environment variables
load_dotenv("env.env", override=True) 
load_dotenv(override=True)

# --- Multiple API Keys for Fallback ---
API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
]
API_KEYS = [k for k in API_KEYS if k]

current_key_index = 0
client = None

# Faster response model
MODEL_NAME = "gemini-2.5-flash"

def init_client(key_index=0):
    global client, current_key_index
    if key_index < len(API_KEYS):
        current_key_index = key_index
        try:
            client = genai.Client(api_key=API_KEYS[key_index])
            print(f"🔑 Using Gemini API Key #{key_index + 1}: {API_KEYS[key_index][:5]}...{API_KEYS[key_index][-3:]}")
            return True
        except Exception as e:
            print(f"❌ Failed to init Gemini with Key #{key_index + 1}: {e}")
            return False
    return False

# Initialize with first key
if API_KEYS:
    init_client(0)
else:
    print("❌ No Gemini API Keys found in env.env!")

SYSTEM_PROMPT = """
You are "Kypzer", an intelligent PC assistant.
Your goal is to understand the user's intent from their message and output valid JSON commands.

You should always try to be helpful and execute the user's commands.

JSON format:
{
  "mode": "TALK" or "HYBRID",
  "say": string (what Kypzer speaks back),
  "steps": [
    {
      "action": one of ["VOLUME_UP", "VOLUME_DOWN", "SET_VOLUME", "MUTE", "UNMUTE",
                       "OPEN_APP", "CLOSE_APP", "SEARCH_WEB", "OPEN_URL", "TYPE_TEXT",
                       "SHUTDOWN", "RESTART", "SLEEP", "LOCK",
                       "SCREENSHOT", "SEARCH_IN_APP", "PRESS_KEYBOARD_KEY", "WAIT", "CLICK_MOUSE", "MOVE_MOUSE",
                       "FLOW_ASMR_VIDEO", "SEND_WHATSAPP", "SEND_WHATSAPP_FILE_SMART", "SEND_WHATSAPP_VOICE_NOTE"],
      "target": string or null,
      "value": number/string/null,
      "confidence": number 0.0 to 1.0
    }
  ]
}

Guidelines:
- Return ONLY valid JSON.
- Personality: You are Kypzer. Helpful, smart, slightly witty.
- For web requests, prefer action "OPEN_URL" when you can infer a reliable exact URL (official site, docs page, known endpoint).
- Use "SEARCH_WEB" only when exact URL is uncertain.
- For file share commands like "papa ko resume bhejo", prefer one action: "SEND_WHATSAPP_FILE_SMART" with value as the full user command text.
- For voice note commands like "mummy ko voice note bhejo ki main late aaunga", use "SEND_WHATSAPP_VOICE_NOTE" with target as contact name and value as note text.
- For plain text WhatsApp messages, use "SEND_WHATSAPP" with target=recipient and value=message.
- If user asks to create/generate ASMR cutting image+video in Google Flow, use one step with action "FLOW_ASMR_VIDEO".
- For FLOW_ASMR_VIDEO, set target to subject (e.g. "apple") and value as object:
    {"subject":"apple", "color":"red", "material":"glass", "surface_effect":"mirror-like", "image_prompt":"...", "video_prompt":"...", "image_timeout":120, "video_timeout":240, "use_recorded_clicks":true}
- If unsure or no command detected: {"mode": "TALK", "say": "I didn't quite catch that.", "steps": []}
"""

def process_multimodal(audio_path=None, text_input=None):
    """
    Voice flow: audio -> online Google speech-to-text -> Gemini (text).
    Text flow: text -> Gemini (text).
    """
    global client, current_key_index

    if not client:
        return None, "API Key Missing"

    # If audio was provided, transcribe it first (do NOT send audio to Gemini)
    if audio_path and not text_input:
        print("🎙️ Transcribing speech to text (Google online STT)...")
        transcript, err = stt.transcribe_wav_google(audio_path)
        if not transcript:
            return None, err or "Speech transcription failed."
        text_input = transcript

    if not text_input:
        return None, "No input provided"

    # Prepare text-only contents for Gemini
    print(f"🧠 Processing Text: {text_input}")
    contents = [SYSTEM_PROMPT, f"User Command: {text_input}"]

    # Try with current key, fallback to next on 429
    for attempt in range(len(API_KEYS)):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents
            )
            
            raw_text = response.text

            # Parse JSON
            try:
                clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)
                return data, raw_text
            except json.JSONDecodeError:
                start = clean_text.find("{")
                end = clean_text.rfind("}")
                if start != -1 and end != -1:
                     return json.loads(clean_text[start:end+1]), raw_text
                return None, raw_text

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"⏳ Rate Limited (429) on Key #{current_key_index + 1}. Switching to next key...")
                next_key = (current_key_index + 1) % len(API_KEYS)
                if init_client(next_key):
                    time.sleep(0.5)
                    continue
                else:
                    print("❌ All API Keys exhausted or failed.")
                    return None, error_str
            else:
                print(f"❌ Gemini Error: {e}")
                return None, error_str
    
    return None, "All retries failed."
