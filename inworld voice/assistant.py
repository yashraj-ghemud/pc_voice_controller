"""
assistant.py - Voice Assistant orchestrator.
Ties the Gemini brain and Inworld voice together.
"""

from brain import GeminiBrain
from voice import InworldVoice


class VoiceAssistant:
    """Personal voice assistant - thinks with Gemini, speaks with Inworld AI."""

    def __init__(self):
        print("")
        print("=" * 46)
        print("       * Nova Voice Assistant *")
        print("  Powered by Gemini AI + Inworld Voice")
        print("=" * 46)
        print("")

        print("[INIT] Loading brain...")
        self.brain = GeminiBrain()

        print("[INIT] Loading voice...")
        self.voice = InworldVoice()

        print("")
        print("[READY] Nova is ready! Type your message and press Enter.")
        print("   Commands: 'exit'/'quit' to leave, 'reset' to clear memory")
        print("")

    def process(self, user_input):
        """
        Process a user message:
        1. Think (Gemini generates response)
        2. Display response text
        3. Speak (Inworld TTS plays audio)
        """
        if not user_input or not user_input.strip():
            return

        # Think
        print("")
        print("  [THINKING...]")
        response_text = self.brain.think(user_input)

        if not response_text:
            print("  [ERROR] No response generated.")
            return

        # Display
        print(f"")
        print(f"  Nova: {response_text}")
        print(f"")

        # Speak
        print("  [SPEAKING...]")
        self.voice.speak(response_text)

    def reset(self):
        """Reset conversation history."""
        self.brain.reset()

    def shutdown(self):
        """Clean up resources."""
        print("")
        print("  [BYE] Nova shutting down... Goodbye!")
        self.voice.cleanup()
        print("")
