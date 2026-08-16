"""
main.py — Entry point for the Nova Voice Assistant.
CLI loop: type a message → Gemini thinks → Inworld speaks.
"""

import sys
from assistant import VoiceAssistant


def main():
    try:
        nova = VoiceAssistant()
    except Exception as e:
        print(f"\n❌ Failed to start Nova: {e}")
        sys.exit(1)

    try:
        while True:
            try:
                user_input = input("  You: ").strip()
            except EOFError:
                break

            # Handle commands
            if user_input.lower() in ("exit", "quit", "bye", "goodbye"):
                nova.shutdown()
                break
            elif user_input.lower() == "reset":
                nova.reset()
                continue
            elif not user_input:
                continue

            # Process the message
            nova.process(user_input)

    except KeyboardInterrupt:
        nova.shutdown()


if __name__ == "__main__":
    main()
