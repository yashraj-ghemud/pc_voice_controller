#nvidia/nemotron-3-super-120b-a12b
#stepfun/step-3.5-flash:free   very advance
#z-ai/glm-4.5-air:free
#
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


HISTORY_FILE = Path(__file__).with_name("chat_history.json")
MODEL_NAME = "stepfun/step-3.5-flash"


def append_history(entry: dict) -> None:
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except (json.JSONDecodeError, OSError):
            history = []

    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def main() -> None:
    api_key = "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"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-OpenRouter-Title": "Local Test Script",
    }

    print("Interactive chatbot started.")
    print("Commands: type your message, 'clear' to reset chat, 'exit' to quit.")

    conversation = []
    while True:
        user_text = input("You: ").strip()

        if not user_text:
            continue

        if user_text.lower() in {"exit", "quit"}:
            print("Chat ended.")
            break

        if user_text.lower() == "clear":
            conversation = []
            print("Conversation cleared.")
            continue

        conversation.append({"role": "user", "content": user_text})
        payload = {
            "model": MODEL_NAME,
            "messages": conversation,
        }
        history_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL_NAME,
            "user_input": user_text,
            "messages": json.loads(json.dumps(conversation)),
        }

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            print("Status:", response.status_code)
            history_entry["status_code"] = response.status_code
            response.raise_for_status()

            data = response.json()
            message = data["choices"][0]["message"]["content"]
            print("Bot:", message)

            conversation.append({"role": "assistant", "content": message})
            history_entry["assistant_reply"] = message
            history_entry["raw_response"] = data
            append_history(history_entry)
        except requests.exceptions.RequestException as exc:
            print("Request failed:", exc)
            history_entry["error"] = str(exc)
            if "response" in locals() and response is not None:
                history_entry["status_code"] = response.status_code
                history_entry["raw_response_text"] = response.text
            append_history(history_entry)
        except (ValueError, KeyError, IndexError, TypeError):
            print("Unexpected response format:")
            if "response" in locals() and response is not None:
                print(response.text)
                history_entry["status_code"] = response.status_code
                history_entry["raw_response_text"] = response.text
            history_entry["error"] = "Unexpected response format"
            append_history(history_entry)


if __name__ == "__main__":
    main()
