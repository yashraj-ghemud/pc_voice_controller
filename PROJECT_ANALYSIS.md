# 🤖 Kypzer AI - Complete Project Analysis

## 📋 Executive Summary
**Kypzer** is an advanced **multimodal AI assistant** for Windows PCs that combines voice control, computer automation, vision AI, and intelligent integrations. It's like having Jarvis from Iron Man on your PC - you speak to it, and it controls your computer.

---

## 🎯 Core Features (What It Can Do)

### 1. **Voice-Controlled PC Automation** 🎤
- **Voice Input**: Records your voice for 5 seconds, converts speech to text using Google STT
- **Voice Output**: Responds using Inworld AI's cloned voice (natural-sounding Hindi/English TTS)
- **Offline Intent Classification**: Handles 50+ common commands locally without API calls
- **Gemini AI Fallback**: Complex commands go to Gemini 2.5 Flash for processing

### 2. **System Control** 💻
**Volume Management**
- Increase/decrease volume
- Set to exact percentage (e.g., "volume 50%")
- Mute/unmute

**Brightness Control**
- Adjust screen brightness up/down
- Set exact brightness level

**Connectivity**
- WiFi on/off
- Bluetooth on/off

**Power Management**
- Shutdown
- Restart
- Sleep
- Lock screen

### 3. **Application Management** 📱
- Open any installed app by name (Chrome, Notepad, VS Code, etc.)
- Close running applications
- Smart app name matching

### 4. **Web & Search** 🌐
- **Fast YouTube Search**: "play [song name] on YouTube" → direct YouTube results
- **Google Search**: Automatically opens search results for queries
- **Direct URL Opening**: Recognizes and opens URLs from speech
- **Web Search**: Generic web queries via Google

### 5. **WhatsApp Automation** 📲
**Three modes of WhatsApp interaction:**

a) **Text Messages**
   - "Papa ko message bhejo ki main late aaunga"
   - Opens chat, types message, sends

b) **Voice Notes**
   - "Mummy ko voice note bhejo ki main ghar pahunch gaya"
   - Converts text to MP3 using TTS
   - Sends as voice note on WhatsApp

c) **Smart File Sharing**
   - "Papa ko resume bhejo"
   - Searches your entire PC for matching files
   - Shows options if multiple found
   - Voice-selects which file to send
   - Copies to clipboard and pastes in WhatsApp

### 6. **Vision AI (Screen Understanding)** 👁️
Powered by **Llama 4 Scout Vision Model** via Groq:

- **Screen Analysis**: "What's on my screen?"
- **Element Finding**: Locates UI elements by description
- **Auto-Clicking**: "Click the play button" → finds and clicks it
- **Smart Typing**: Finds input fields and types text
- **Visual Condition Checking**: Waits for specific UI states

### 7. **Media Controls** 🎵
- Play/Pause media
- Next/Previous track
- Stop playback
- Works with any media player

### 8. **Virtual Desktop Management** 🖥️
- Switch between virtual desktops (Win+Ctrl+Left/Right)
- Navigate between workspaces

### 9. **Input Automation** ⌨️
- Type text (Unicode/Hindi support via clipboard)
- Press keyboard shortcuts
- Mouse click/move operations
- Screenshot capture

### 10. **Google Flow ASMR Video Generator** 🎬
**Advanced automation tool** for creating ASMR cutting videos:

- **Grabifier Tool**: Records mouse coordinates and click sequences
- **Flow Automation**: 15-step coded workflow
- **Image Generation**: Creates hyper-realistic glass object images
- **Video Generation**: Converts images to ASMR cutting videos
- **Smart Waiting**: Uses vision AI to detect generation completion
- **Auto-Download**: Downloads finished videos automatically

### 11. **Memory System** 🧠
- **ChromaDB Vector Database**: Stores conversation history
- **Gemini Embeddings**: Semantic search through past conversations
- **Context Retrieval**: Relevant past conversations auto-included

---

## 🏗️ Technical Architecture

### Core Components

```
┌─────────────────────────────────────────────────┐
│                   main.py                       │
│            (Entry Point & Controller)           │
└────────────┬────────────────────────────────────┘
             │
     ┌───────┴───────┐
     │               │
     v               v
┌─────────┐    ┌──────────┐
│  mic.py │    │  stt.py  │
│ (Audio) │    │ (Google) │
└─────────┘    └──────────┘
     │               │
     v               v
┌──────────────────────────┐
│      intent.py           │
│ (Offline Classification) │
└─────────┬────────────────┘
          │
    ┌─────┴─────┐
    │   Found?  │
    └──┬─────┬──┘
       │     │
    Yes│     │No
       │     │
       v     v
  ┌────────┐ ┌──────────┐
  │actions │ │ brain.py │
  │  .py   │ │ (Gemini) │
  └────────┘ └──────────┘
       │          │
       └────┬─────┘
            v
       ┌─────────┐
       │ tts.py  │
       │(Inworld)│
       └─────────┘
```

### File Structure

**Core System**
- `main.py` - Main event loop, command routing, fast routes
- `brain.py` - Gemini AI integration, JSON action extraction
- `actions.py` - All PC automation actions (891 lines)
- `intent.py` - Offline intent classifier with Hindi responses

**Voice I/O**
- `mic.py` - Microphone recording (5s fixed or VAD)
- `stt.py` - Google Speech-to-Text
- `tts.py` - Inworld AI Text-to-Speech (cloned voice)

**AI Features**
- `screen_ai.py` - Vision AI with Llama 4 Scout
- `memory.py` - ChromaDB conversation memory

**Automation Tools**
- `grabifier.py` - Mouse coordinate recorder for Flow automation
- `flow` functions in `actions.py` - Google Flow ASMR pipeline

**WhatsApp Module**
- `handler.py` - Command parsing, file search, voice notes
- `wa_controller.py` - WhatsApp Desktop automation
- `tts.py` - Voice note MP3 generation
- `file_search.py` - PC-wide file search
- `clipboard.py` - File clipboard operations
- `utils.py` - Helper functions
- `config.py` - Configuration

**Configuration**
- `env.env` - API keys and secrets

---

## 🔑 API Keys & Services Used

1. **Google Gemini** - Main AI brain (4 keys for rate limiting)
2. **Inworld AI** - Voice cloning TTS
3. **Groq** - Vision AI (Llama 4 Scout) + Backup chat
4. **Google STT** - Speech-to-text (free)

---

## 💡 How It Works (Flow Example)

**User says:** *"Papa ko resume bhejo"*

```
1. mic.py records 5 seconds of audio
2. stt.py converts to text: "papa ko resume bhejo"
3. main.py checks _fast_whatsapp_route() → matches!
4. Returns: {"action": "SEND_WHATSAPP_FILE_SMART", "value": "papa ko resume bhejo"}
5. actions.execute_steps() calls WhatsApp handler
6. handler.py:
   - Parses: contact="papa", keyword="resume"
   - file_search.py searches PC for "resume"
   - Finds: resume.pdf, resume_old.pdf
   - tts.speak_async("Mujhe 2 files mili...")
   - mic.py records selection
   - User says: "pehli" (first one)
   - clipboard.py copies resume.pdf
7. wa_controller.py:
   - Opens WhatsApp Desktop
   - Ctrl+F → types "papa" → Enter
   - Ctrl+V → pastes file → Enter
8. tts.speak_async("resume.pdf bhej diya!")
9. Done ✅
```

---

## 🚀 Advanced Features

### Fast Route Optimization
**Problem**: Gemini API calls add 2-3 second delay  
**Solution**: Pattern-matched "fast routes" in `main.py`
- YouTube queries → direct YouTube URL
- Web searches → direct Google URL
- WhatsApp commands → instant handler call
- **Result**: Sub-second response for common tasks

### Multi-Key Rate Limiting
```python
API_KEYS = [key1, key2, key3, key4]
# On 429 error → auto-switch to next key
```

### Vision AI Integration
- Takes screenshot → encodes to base64
- Sends to Llama 4 Scout with prompt
- Parses JSON response for coordinates
- Clicks/types at exact pixels

### Flow Automation System
**15-Step Coded Sequence:**
1. Open Flow project
2. Select image mode
3. Paste image prompt
4. Generate image
5. Wait for completion (vision AI checks every 3s)
6. Switch to video mode
7. Add generated image
8. Paste video prompt
9. Generate video
10. Wait for completion (vision AI checks every 5s)
11-15. Download workflow

---

## 📦 Dependencies

**Core**
- `google-generativeai` - Gemini AI
- `groq` - Vision AI & backup chat
- `pyautogui` - Automation
- `pycaw` - Volume control
- `keyboard` - Keyboard input
- `pyperclip` - Clipboard operations

**Voice**
- `speech_recognition` - Google STT
- `pyaudio` - Microphone
- `pygame` - Audio playback
- `requests` - Inworld TTS API

**AI/ML**
- `chromadb` - Vector DB for memory
- `pillow` - Image processing
- `mss` - Screenshots

**WhatsApp**
- `pygetwindow` - Window management
- `gtts` - Voice note TTS

---

## 🎯 Use Cases

1. **Hands-Free PC Control**: Cook while controlling music, volume, apps
2. **Quick Web Searches**: Instant YouTube/Google without typing
3. **WhatsApp Automation**: Send files/voice notes without manual search
4. **Accessibility**: Full PC control via voice for disabled users
5. **Content Creation**: Automated ASMR video generation
6. **Smart Home**: Basis for integrating with home automation
7. **Productivity**: Quick screenshot, clipboard, virtual desktop switching

---

## ⚠️ Current Limitations

1. **Windows Only**: Uses Win32 APIs, PowerShell, pycaw
2. **Fixed Recording**: 5-second voice input (no dynamic VAD by default)
3. **English/Hindi Only**: STT language set to en-IN
4. **WhatsApp Desktop Required**: No WhatsApp Web support
5. **No Wake Word**: Manual activation (press Enter)
6. **API Key Dependency**: Requires 3+ API keys to function
7. **No Error Recovery**: Some actions fail silently

---
