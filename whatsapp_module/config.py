import os


CONFIG = {
    "DELAY_SHORT": 0.5,
    "DELAY_MEDIUM": 1.5,
    "DELAY_LONG": 3.0,
    "TEMP_DIR": "temp",
    "EVERYTHING_PATH": r"C:/Program Files/Everything/es.exe",
    "TESTING_MODE": True,
    "VOICE_NOTE_FORCE_SEND": True,
    "TEMP_FILE_DELETE_DELAY": 10,
    "TTS_LANG": "hi",
    "TTS_MAX_RETRIES": 3,
    "TTS_MIN_BYTES": 2048,
    "MAX_SEARCH_RESULTS": 5,
    "INWORLD_TTS_URL": "https://api.inworld.ai/tts/v1/voice",
    "INWORLD_VOICE_ID": "default-5s-jukkvfx169axixzqasw__yashraj-lpyj1",
    "INWORLD_MODEL_ID": "inworld-tts-1.5-max",
    "INWORLD_SPEAKING_RATE": 0.93,
    "INWORLD_TEMPERATURE": 1.01,
    "SEARCH_ROOTS": [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents"),
        r"C:/",
    ],
    "EXCLUDE_DIR_NAMES": {
        "Windows",
        "System32",
        "$Recycle.Bin",
        "node_modules",
        "Temp",
    },
    "FALLBACK_WORKERS": 8,
}
