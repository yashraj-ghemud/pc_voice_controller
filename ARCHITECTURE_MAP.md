# 🏗️ Kypzer AI - System Architecture Map

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                                                                 │
│  🎤 Voice Input (5s recording)  ⌨️ Text Input (keyboard)      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT PROCESSING                           │
│                                                                 │
│  ┌──────────┐         ┌──────────────┐                        │
│  │ mic.py   │────────>│   stt.py     │                        │
│  │(PyAudio) │         │(Google STT)  │                        │
│  └──────────┘         └──────┬───────┘                        │
│                              │                                 │
│                              v                                 │
│                    📝 Transcript Text                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               v
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTING & CLASSIFICATION                     │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           main.py - Fast Route Detection               │   │
│  │                                                         │   │
│  │  🚀 _fast_browser_route()     → Direct URLs           │   │
│  │  📲 _fast_whatsapp_route()    → WhatsApp Handler      │   │
│  └────────────┬───────────────────────────┬────────────────┘   │
│               │ No Match                  │ Match              │
│               v                           v                     │
│  ┌─────────────────────┐      ┌──────────────────────┐        │
│  │    intent.py        │      │  Execute Directly    │        │
│  │ Offline Classifier  │      │  (sub-second)        │        │
│  │  - 50+ patterns     │      └──────────────────────┘        │
│  │  - Hindi responses  │                                       │
│  └──────┬──────────────┘                                       │
│         │ No Match                                             │
│         v                                                      │
│  ┌─────────────────────┐                                       │
│  │     brain.py        │                                       │
│  │  Gemini 2.5 Flash   │                                       │
│  │  - JSON extraction  │                                       │
│  │  - 4-key rotation   │                                       │
│  └──────┬──────────────┘                                       │
│         │                                                      │
│         v                                                      │
│  {"say": "...", "steps": [...]}                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│                      ACTION EXECUTION                           │
│                         (actions.py)                            │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │ System Control │  │ App Management │  │  Web & Search   │ │
│  │                │  │                │  │                 │ │
│  │ • Volume       │  │ • Open apps    │  │ • YouTube      │ │
│  │ • Brightness   │  │ • Close apps   │  │ • Google       │ │
│  │ • WiFi/BT      │  │ • Smart match  │  │ • Open URLs    │ │
│  │ • Power mgmt   │  └────────────────┘  └─────────────────┘ │
│  └────────────────┘                                           │
│                                                                │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │ Media Controls │  │ Input Control  │  │  WhatsApp       │ │
│  │                │  │                │  │                 │ │
│  │ • Play/Pause   │  │ • Type text    │  │ • Text msgs    │ │
│  │ • Next/Prev    │  │ • Keyboard     │  │ • Voice notes  │ │
│  │ • Stop         │  │ • Mouse click  │  │ • File share   │ │
│  └────────────────┘  │ • Screenshot   │  └─────────────────┘ │
│                      └────────────────┘                        │
│                                                                │
│  ┌────────────────┐  ┌────────────────┐                       │
│  │  Vision AI     │  │  Flow ASMR     │                       │
│  │ (screen_ai.py) │  │  Automation    │                       │
│  │                │  │                │                       │
│  │ • Find element │  │ • Image gen    │                       │
│  │ • Click UI     │  │ • Video gen    │                       │
│  │ • Type in field│  │ • Download     │                       │
│  │ • Wait condition│  │ • 15-step flow│                       │
│  └────────────────┘  └────────────────┘                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT & FEEDBACK                          │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │   tts.py     │────────>│  Speaker 🔊  │                    │
│  │(Inworld AI)  │         └──────────────┘                    │
│  └──────────────┘                                              │
│                                                                │
│  ┌──────────────┐                                              │
│  │  memory.py   │  Stores conversation in ChromaDB            │
│  │(ChromaDB)    │  for future context retrieval               │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

### Scenario 1: Simple Command (Offline)
```
User: "Volume badha"
    ↓
mic.py → records audio
    ↓
stt.py → "volume badha"
    ↓
main.py → checks fast routes (no match)
    ↓
intent.py → matches VOLUME_UP pattern
    ↓
    Returns: {
        "action": "VOLUME_UP",
        "say": "वॉल्यूम बढ़ा दिया बाबू!"
    }
    ↓
actions.change_volume(+10)
    ↓
tts.speak_async("वॉल्यूम बढ़ा दिया बाबू!")
    ↓
Done ✅ (sub-second execution)
```

### Scenario 2: Fast Route (Browser)
```
User: "Play Arijit Singh songs on YouTube"
    ↓
mic.py → records
    ↓
stt.py → transcript
    ↓
main.py._fast_browser_route() → MATCH!
    ↓
    Constructs: https://youtube.com/results?search_query=Arijit+Singh+songs
    ↓
    Returns: {
        "say": "Opening YouTube results for Arijit Singh songs",
        "steps": [{"action": "OPEN_URL", "value": "..."}]
    }
    ↓
actions.open_url(url)
    ↓
webbrowser.open(url)
    ↓
Done ✅ (sub-second execution)
```

### Scenario 3: Complex Command (Gemini AI)
```
User: "Create an ASMR video of glass strawberry being cut"
    ↓
mic.py → records
    ↓
stt.py → transcript
    ↓
main.py → no fast route match
    ↓
intent.py → no pattern match
    ↓
brain.py → Gemini 2.5 Flash API call
    ↓
    System Prompt: "You are Kypzer, return JSON..."
    User Input: transcript
    ↓
    Gemini Response: {
        "mode": "HYBRID",
        "say": "Creating ASMR cutting video for glass strawberry",
        "steps": [{
            "action": "FLOW_ASMR_VIDEO",
            "target": "strawberry",
            "value": {
                "subject": "strawberry",
                "color": "red",
                "material": "glass",
                ...
            }
        }]
    }
    ↓
actions.execute_steps(steps)
    ↓
actions.run_flow_image_to_video()
    ↓
    1. Opens Google Flow
    2. Generates image
    3. Waits (screen_ai checks completion)
    4. Generates video
    5. Downloads
    ↓
Done ✅ (2-3 minutes)
```

### Scenario 4: WhatsApp Smart File Share
```
User: "Papa ko resume bhejo"
    ↓
mic.py → records
    ↓
stt.py → "papa ko resume bhejo"
    ↓
main.py._fast_whatsapp_route() → MATCH!
    ↓
    Returns: {
        "say": "Theek hai, file dhoondhkar WhatsApp par bhej rahi hoon",
        "steps": [{
            "action": "SEND_WHATSAPP_FILE_SMART",
            "value": "papa ko resume bhejo"
        }]
    }
    ↓
whatsapp_module.handler.handle_send_command()
    ↓
    1. Parses: contact="papa", keyword="resume"
    2. file_search.search_files("resume")
       → searches C:/, D:/ for *resume*
       → finds: resume.pdf, resume_backup.pdf
    3. tts.speak("Mujhe 2 files mili. 1. resume.pdf, 2. resume_backup...")
    4. mic.listen_once()
       → User: "pehli"
    5. utils.extract_number_from_speech("pehli") → 1
    6. Selects: resume.pdf
    7. clipboard.copy_file_to_clipboard(resume.pdf)
    8. wa_controller.open_whatsapp_chat("papa")
       → Opens WhatsApp Desktop
       → Ctrl+F → types "papa" → Enter
    9. wa_controller.paste_and_send()
       → Ctrl+V → Enter
    10. tts.speak("resume.pdf bhej diya!")
    ↓
Done ✅
```

---

## 🧩 Module Dependency Graph

```
main.py
  ├── mic.py
  ├── stt.py
  │     └── speech_recognition
  ├── tts.py
  │     ├── pygame
  │     ├── requests (Inworld API)
  │     └── dotenv
  ├── intent.py (no external deps)
  ├── brain.py
  │     ├── google.genai
  │     └── stt.py
  ├── actions.py
  │     ├── pyautogui
  │     ├── keyboard
  │     ├── pycaw (volume)
  │     ├── AppOpener
  │     ├── webbrowser
  │     ├── screen_ai.py
  │     └── whatsapp_module/
  │           ├── handler.py
  │           ├── wa_controller.py
  │           ├── file_search.py
  │           ├── clipboard.py
  │           ├── tts.py
  │           └── config.py
  ├── memory.py
  │     ├── chromadb
  │     └── google.genai (embeddings)
  └── screen_ai.py
        ├── groq (Llama 4 Scout)
        ├── mss (screenshots)
        ├── pyautogui
        └── PIL
```

---

## 🔐 API Integration Points

```
┌─────────────────────────────────────────────┐
│           External Services                 │
└─────────────────────────────────────────────┘

1. Google Gemini API
   ├── Endpoint: generativelanguage.googleapis.com
   ├── Model: gemini-2.5-flash
   ├── Purpose: Main AI brain, command interpretation
   └── Rate Limit: Handled with 4-key rotation

2. Google STT (Web Speech API)
   ├── Library: speech_recognition
   ├── Language: en-IN
   ├── Purpose: Voice to text
   └── Free tier

3. Inworld AI
   ├── Endpoint: api.inworld.ai/tts/v1/voice
   ├── Voice: custom cloned voice
   ├── Purpose: Text to speech
   └── API Key: INWORLD_API_KEY

4. Groq
   ├── Model: meta-llama/llama-4-scout-17b-16e-instruct
   ├── Purpose: Vision AI (screenshot analysis)
   └── API Key: hardcoded in screen_ai.py

5. Google Flow (no API)
   ├── Type: Browser automation
   ├── Purpose: ASMR video generation
   └── Method: Coordinate-based clicks + Vision AI

6. WhatsApp Desktop (no API)
   ├── Type: Desktop automation
   ├── Method: PyAutoGUI keyboard simulation
   └── Purpose: Message/file sending
```

---

## 💾 Data Storage

```
1. Conversation Memory
   ├── Location: ./chroma_db/
   ├── Type: Vector database (ChromaDB)
   ├── Content: User messages + assistant responses
   └── Embeddings: Gemini text-embedding-004

2. Configuration
   ├── File: env.env
   ├── Content: API keys, secrets
   └── Format: KEY=value

3. Temporary Files
   ├── Location: ./
   ├── Files:
   │   ├── input.wav (voice recording)
   │   ├── screenshot_*.png
   │   └── WhatsApp voice notes (temp/*)
   └── Cleanup: Auto-deleted after use

4. Logs
   ├── Grabifier: grabifier_log_*.json/csv
   ├── Chat History: chat_history.json
   └── Generated Images: generated_images/
```

---

## 🔌 Hardware I/O

```
INPUT
├── Microphone
│   ├── Library: PyAudio
│   ├── Format: 16-bit PCM, 44.1kHz, Mono
│   └── Duration: 5 seconds (or VAD)
├── Keyboard
│   └── Library: keyboard
└── Mouse
    └── Library: pyautogui

OUTPUT
├── Speaker
│   ├── Library: pygame.mixer
│   └── Format: MP3/WAV
├── Display
│   ├── Screenshots: mss
│   └── Automation: pyautogui
└── System APIs
    ├── Volume: pycaw (Windows Core Audio)
    ├── Brightness: WMI (PowerShell)
    └── WiFi/BT: netsh, PowerShell
```

---

## ⚡ Performance Characteristics

| Action Type | Latency | Notes |
|-------------|---------|-------|
| Offline Intent (volume, brightness) | <0.5s | Instant pattern match |
| Fast Route (YouTube, WhatsApp) | <0.8s | Direct URL/handler |
| Gemini AI Call | 2-3s | Network + inference |
| Vision AI (screen analysis) | 3-5s | Screenshot + Groq API |
| WhatsApp File Search | 5-15s | Depends on file count |
| Flow ASMR Video | 2-5min | Image (1-2min) + Video (1-3min) |
| Voice Note Send | 8-12s | TTS + WhatsApp automation |

---

## 🛠️ Technology Stack Summary

**Language**: Python 3.10+

**AI/ML**
- Google Gemini (LLM)
- Groq Llama 4 Scout (Vision)
- ChromaDB (Vector DB)
- Gemini Embeddings

**Voice**
- PyAudio (recording)
- speech_recognition (STT)
- Inworld AI (TTS)
- pygame (playback)

**Automation**
- PyAutoGUI (mouse/keyboard)
- keyboard (hotkeys)
- pycaw (volume)
- AppOpener (apps)

**UI/Screen**
- mss (screenshots)
- PIL (image processing)
- pygetwindow (window management)

**Utilities**
- pyperclip (clipboard)
- python-dotenv (config)
- requests (HTTP)

---

## 📊 System Requirements

**Minimum**
- Windows 10/11
- 4GB RAM
- Microphone + Speaker
- Internet connection

**Recommended**
- Windows 11
- 8GB RAM
- Good quality USB mic
- Fast internet (for Gemini/Groq)

**API Requirements**
- Google Gemini API key(s)
- Inworld AI API key
- Groq API key

---

This architecture map shows how Kypzer is a **well-engineered multi-layer system** with clear separation of concerns, smart routing for performance, and extensive integration capabilities.
