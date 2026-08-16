import json
import time
import re
from urllib.parse import quote_plus
import brain
import actions
import tts
import intent
import mic
import stt
import os

# Agent system imports
from agents.init import get_orchestrator, initialize_agent_system
from agents.config import get_config

# Voice mode enabled: assistant will speak responses via TTS.
TEXT_ONLY_MODE = False


def _extract_url(text):
    m = re.search(r"(https?://\S+|www\.\S+)", text, flags=re.IGNORECASE)
    return m.group(1) if m else None


def _fast_browser_route(transcript):
    """Return immediate OPEN_URL steps for common browsing tasks."""
    if not transcript:
        return None

    text = transcript.strip()
    lower = text.lower()

    explicit_url = _extract_url(text)
    if explicit_url:
        return {
            "say": "Opening the URL now.",
            "steps": [{"action": "OPEN_URL", "target": None, "value": explicit_url}],
        }

    # YouTube intents: search/watch/play on YouTube -> direct YouTube search URL.
    yt_markers = ["youtube", "yt", "watch", "play"]
    asks_yt = ("youtube" in lower) or (" on yt" in lower) or (" on youtube" in lower)
    if asks_yt or ("watch" in lower and any(k in lower for k in yt_markers)):
        q = re.sub(r"\b(search|find|play|watch|on|in|youtube|yt|video|videos|for)\b", " ", lower, flags=re.IGNORECASE)
        q = re.sub(r"\s+", " ", q).strip()
        if not q:
            q = text
        url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
        return {
            "say": f"Opening YouTube results for {q}.",
            "steps": [{"action": "OPEN_URL", "target": None, "value": url}],
        }

    # Generic browser/web search intents -> direct Google query URL.
    web_markers = ["search", "google", "find", "look up", "browse", "web", "best", "top", "under"]
    if any(m in lower for m in web_markers):
        q = re.sub(r"\b(search|google|find|look up|browse|web|for|on)\b", " ", text, flags=re.IGNORECASE)
        q = re.sub(r"\s+", " ", q).strip() or text
        url = f"https://www.google.com/search?q={quote_plus(q)}"
        return {
            "say": f"Opening search results for {q}.",
            "steps": [{"action": "OPEN_URL", "target": None, "value": url}],
        }

    return None


def _fast_whatsapp_route(transcript):
    """Return immediate WhatsApp send steps for voice note and file commands."""
    if not transcript:
        return None

    text = transcript.strip()
    lower = text.lower()

    # Voice note command examples:
    # - "papa ko voice note bhejo ki mai late aaunga"
    # - "send voice note to papa saying mai late aaunga"
    if ("voice note" in lower or "audio note" in lower) and ("bhejo" in lower or "send" in lower):
        m = re.search(r"(.+?)\s+ko\s+(?:voice\s*note|audio\s*note)\s+bhejo\s*(.*)", text, flags=re.IGNORECASE)
        if m:
            contact = m.group(1).strip()
            msg = (m.group(2) or "").strip()
            msg = re.sub(r"^(ki|that|saying)\s+", "", msg, flags=re.IGNORECASE).strip()
            if not msg:
                msg = "Namaste"
            return {
                "say": f"{contact} ko voice note bhej rahi hoon.",
                "steps": [{"action": "SEND_WHATSAPP_VOICE_NOTE", "target": contact, "value": msg}],
            }

        m = re.search(
            r"send\s+(?:a\s+)?(?:voice\s*note|audio\s*note)\s+to\s+(.+?)\s+(?:saying|that)\s+(.+)",
            text,
            flags=re.IGNORECASE,
        )
        if m:
            contact = m.group(1).strip()
            msg = m.group(2).strip()
            return {
                "say": f"Sending a voice note to {contact}.",
                "steps": [{"action": "SEND_WHATSAPP_VOICE_NOTE", "target": contact, "value": msg}],
            }

    # Smart file send command examples:
    # - "papa ko resume bhejo"
    # - "send resume to papa"
    if "bhejo" in lower and "ko" in lower and not ("voice note" in lower or "audio note" in lower):
        return {
            "say": "Theek hai, file dhoondhkar WhatsApp par bhej rahi hoon.",
            "steps": [{"action": "SEND_WHATSAPP_FILE_SMART", "target": None, "value": text}],
        }

    m = re.search(r"send\s+(.+?)\s+to\s+(.+)", text, flags=re.IGNORECASE)
    if m and not ("voice note" in lower or "audio note" in lower):
        inferred = f"{m.group(2).strip()} ko {m.group(1).strip()} bhejo"
        return {
            "say": "Okay, searching and preparing the file to send on WhatsApp.",
            "steps": [{"action": "SEND_WHATSAPP_FILE_SMART", "target": None, "value": inferred}],
        }

    return None

def main():
    print("\n" + "="*50)
    print("🤖 Kypzer AI (Gemini 2.0 Flash) - Native Multimodal")
    if TEXT_ONLY_MODE:
        print("⌨️ Text-only mode is ON (voice input/output paused).")
        print("⌨️ Type your command and press ENTER.")
    else:
        print("🎤 Press ENTER to start recording (5 seconds).")
    print("❌ Type 'exit' to quit.")
    print("="*50 + "\n")
    
    # Initialize agent system at startup (Requirement 17.2, 20.4)
    config = get_config()
    orchestrator = None
    agent_system_available = False
    
    if config.is_agent_system_enabled():
        print("🚀 Initializing Agent System...")
        success, orch, error = initialize_agent_system()
        if success:
            orchestrator = orch
            agent_system_available = True
            print("✅ Agent System ready!\n")
        else:
            print(f"⚠️ Agent System init failed: {error}")
            print("🔄 Falling back to legacy mode\n")
    else:
        print(f"ℹ️  Mode: {config.get_mode_description()}\n")

    while True:
        try:
            if TEXT_ONLY_MODE:
                user_input = input("🟢 Enter command (or type 'exit'): ").strip()
            else:
                user_input = input("🟢 Press ENTER to speak (or type 'exit'): ").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Goodbye!")
                if not TEXT_ONLY_MODE:
                    tts.speak("Goodbye! Shutting down systems.")
                break
            
            if TEXT_ONLY_MODE:
                # In text-only mode, ignore empty input and wait for typed command.
                if not user_input:
                    continue
                transcript = user_input

            # If user typed a command, skip recording and send text directly
            elif user_input:
                transcript = user_input
            else:
                # --- 1. RECORD AUDIO ---
                audio_file = mic.record_audio()

                if not audio_file or not os.path.exists(audio_file):
                    print("⚠️ Audio recording failed.")
                    continue

                # --- 2. SPEECH TO TEXT (Online Google) ---
                print("📝 Converting speech to text...")
                transcript, stt_err = stt.transcribe_wav_google(audio_file)

                # Remove audio file after transcription to keep clean
                try:
                    os.remove(audio_file)
                except:
                    pass

                if not transcript:
                    print(f"⚠️ STT failed: {stt_err}")
                    continue

            print(f"🗣️ You said: {transcript}")

            # --- 3. SUPER-FAST WHATSAPP ROUTING ---
            fast_wa = _fast_whatsapp_route(transcript)
            if fast_wa:
                say_text = fast_wa.get("say", "")
                steps = fast_wa.get("steps", [])
                print("⚡ Fast WhatsApp route matched")
            else:
                # --- 3. SUPER-FAST BROWSER ROUTING ---
                fast_web = _fast_browser_route(transcript)
                if fast_web:
                    say_text = fast_web.get("say", "")
                    steps = fast_web.get("steps", [])
                    print("⚡ Fast browser route matched")
                else:
                    # --- 3. FAST LOCAL INTENT FIRST ---
                    local = intent.classify(transcript)
                    # Let Gemini handle web queries so it can return exact OPEN_URL links.
                    if local and local.get("action") == "SEARCH_WEB":
                        local = None
                    if local:
                        say_text = local.get("say", "")
                        steps = [{
                            "action": local.get("action"),
                            "target": local.get("target"),
                            "value": local.get("value"),
                        }]
                        print("⚡ Fast local intent matched")
                    else:
                        # --- 4. AGENT SYSTEM OR LEGACY BRAIN ---
                        # Requirement 16.1, 16.2, 16.3: Route to agent system or legacy
                        if agent_system_available and orchestrator:
                            try:
                                print("🤖 Agent System processing...")
                                
                                # Process through orchestrator (Requirement 16.3)
                                result = orchestrator.process_command(
                                    transcript,
                                    context={}
                                )
                                
                                if result.get("success"):
                                    # Extract response from agent result
                                    agent_result = result.get("result", {})
                                    
                                    if result.get("used_fast_route"):
                                        # Fast route executed
                                        say_text = agent_result.get("say", "Done")
                                        steps = [{
                                            "action": agent_result.get("action"),
                                            "target": agent_result.get("target"),
                                            "value": agent_result.get("value"),
                                        }]
                                        print("⚡ Agent system fast route")
                                    else:
                                        # Graph workflow executed
                                        final_result = agent_result.get("final_result") if agent_result else None
                                        
                                        if final_result and final_result.get("success"):
                                            # Get response from last agent
                                            responses = final_result.get("agent_responses", [])
                                            if responses:
                                                last_response = responses[-1]
                                                result_data = last_response.get("result", {})
                                                say_text = result_data.get("say", "Task completed")
                                                steps = result_data.get("steps", [])
                                            else:
                                                say_text = "Task completed"
                                                steps = []
                                            print("✅ Agent workflow completed")
                                        else:
                                            # Agent workflow failed
                                            error = final_result.get("error") if final_result else "Unknown error"
                                            say_text = f"Sorry, I encountered an error: {error}"
                                            steps = []
                                            print(f"⚠️ Agent workflow failed: {error}")
                                else:
                                    # Agent system error - fallback (Requirement 17.4)
                                    error = result.get("error", "Unknown error")
                                    print(f"⚠️ Agent system error: {error}")
                                    print("🔄 Falling back to legacy brain...")
                                    
                                    # Fallback to legacy (Requirement 12.2, 23.3)
                                    data, raw_output = brain.process_multimodal(text_input=transcript)
                                    if not data:
                                        print(f"⚠️ Debug Raw: {raw_output}")
                                        print("⚠️ No valid JSON returned.")
                                        continue
                                    say_text = data.get("say", "")
                                    steps = data.get("steps", [])
                                    
                            except Exception as e:
                                # Agent system exception - fallback (Requirement 17.4)
                                print(f"❌ Agent system exception: {e}")
                                print("🔄 Falling back to legacy brain...")
                                
                                data, raw_output = brain.process_multimodal(text_input=transcript)
                                if not data:
                                    print(f"⚠️ Debug Raw: {raw_output}")
                                    print("⚠️ No valid JSON returned.")
                                    continue
                                say_text = data.get("say", "")
                                steps = data.get("steps", [])
                        else:
                            # Legacy brain path (Requirement 16.4)
                            print("🧠 Kypzer is thinking...")
                            data, raw_output = brain.process_multimodal(text_input=transcript)

                            if not data:
                                print(f"⚠️ Debug Raw: {raw_output}")
                                print("⚠️ No valid JSON returned.")
                                continue

                            say_text = data.get("say", "")
                            steps = data.get("steps", [])

            # If empty response (ignored command due to no wake word), loop back
            if not say_text and not steps:
                print("😶 [Ignored - No Wake Word]")
                continue

            # --- 5. SPEAK RESPONSE ---
            if say_text:
                print(f"🤖 Kypzer: {say_text}")
                if not TEXT_ONLY_MODE:
                    tts.speak_async(say_text)

            # --- 6. EXECUTE ACTIONS ---
            if steps:
                print("\n⚙️ Executing Actions...")
                actions.execute_steps(steps)
                print("✅ Done.\n")

        except KeyboardInterrupt:
            print("\n👋 Force Quit.")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")

if __name__ == "__main__":
    main()
