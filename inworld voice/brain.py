"""
brain.py - Gemini AI thinking module with multi-key rotation.
Handles conversation history and intelligent response generation.
"""

import time
import json
import os
from google import genai
import config

HISTORY_FILE = "conversation_history.json"


class GeminiBrain:
    """AI brain powered by Gemini with automatic API key rotation."""

    def __init__(self):
        self.client = None
        self.current_key_index = 0
        self.conversation_history = self._load_history()

        if not config.GEMINI_API_KEYS:
            raise RuntimeError("[ERROR] No Gemini API keys found in .env!")

        self._init_client(0)

    def _load_history(self):
        """Load conversation history from file if it exists."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    print(f"  [LOAD] Loaded {len(history)} messages from history.")
                    return history
            except Exception as e:
                print(f"  [ERROR] Failed to load history: {e}")
        return []

    def _save_history(self):
        """Save conversation history to file."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [ERROR] Failed to save history: {e}")

    def _init_client(self, key_index=0):
        """Initialize Gemini client with the given API key index."""
        if key_index < len(config.GEMINI_API_KEYS):
            self.current_key_index = key_index
            key = config.GEMINI_API_KEYS[key_index]
            try:
                self.client = genai.Client(api_key=key)
                print(f"  [KEY] Gemini Key #{key_index + 1}: {key[:8]}...{key[-4:]}")
                return True
            except Exception as e:
                print(f"  [ERROR] Failed to init Key #{key_index + 1}: {e}")
                return False
        return False

    def _build_prompt(self, user_message):
        """Build the full prompt with system instruction + conversation history."""
        self.conversation_history.append({"role": "user", "text": user_message})
        self._save_history()

        # Keep history manageable to save tokens
        if len(self.conversation_history) > config.MAX_HISTORY_MESSAGES:
            self.conversation_history = self.conversation_history[-config.MAX_HISTORY_MESSAGES:]

        parts = [config.SYSTEM_PROMPT, ""]

        if len(self.conversation_history) > 1:
            parts.append("--- Conversation so far ---")
            for msg in self.conversation_history[:-1]:
                role = "User" if msg["role"] == "user" else "Nova"
                parts.append(f"{role}: {msg['text']}")
            parts.append("--- End of history ---")
            parts.append("")

        parts.append(f"User: {user_message}")
        parts.append("")
        parts.append("Respond naturally and concisely (1-3 sentences). No emojis or markdown.")

        return "\n".join(parts)

    def think(self, user_message):
        """
        Process user message through Gemini with automatic key rotation.
        Returns the AI response text.
        """
        prompt = self._build_prompt(user_message)

        for attempt in range(len(config.GEMINI_API_KEYS)):
            try:
                key_idx = (self.current_key_index + attempt) % len(config.GEMINI_API_KEYS)
                if attempt > 0:
                    self._init_client(key_idx)

                response = self.client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt,
                )

                ai_text = response.text.strip()
                self.conversation_history.append({"role": "assistant", "text": ai_text})
                self._save_history()
                return ai_text

            except Exception as e:
                print(f"  [WARN] Gemini Key #{key_idx + 1} failed: {e}")
                if attempt < len(config.GEMINI_API_KEYS) - 1:
                    print("  [ROTATE] Switching to next API key...")
                    time.sleep(1)
                else:
                    print("  [ERROR] All API keys exhausted!")
                    return "I'm having trouble thinking right now. Please try again in a moment."

    def reset(self):
        """Clear conversation history."""
        self.conversation_history = []
        self._save_history()
        print("  [RESET] Conversation history cleared.")
