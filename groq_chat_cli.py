import json
import os
import sys
import urllib.error
import urllib.request


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"
HARDCODED_GROQ_API_KEY = "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"


def load_env_file(env_file_path: str) -> None:
	"""Load key=value pairs from env.env into process environment if missing."""
	if not os.path.exists(env_file_path):
		return

	try:
		with open(env_file_path, "r", encoding="utf-8") as file:
			for line in file:
				line = line.strip()
				if not line or line.startswith("#") or "=" not in line:
					continue
				key, value = line.split("=", 1)
				key = key.strip()
				value = value.strip().strip('"').strip("'")
				if key and key not in os.environ:
					os.environ[key] = value
	except OSError:
		# Non-fatal: user can still set key through environment or prompt.
		return


def get_api_key() -> str:
	if HARDCODED_GROQ_API_KEY and HARDCODED_GROQ_API_KEY.startswith("gsk_"):
		return HARDCODED_GROQ_API_KEY

	key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
	if key and key != "gsk_your_real_key_here":
		return key

	print("\nGROQ_API_KEY not found in environment.")
	print("Paste your Groq key (input hidden in terminal history is not guaranteed).")
	key = input("GROQ_API_KEY: ").strip().strip('"').strip("'")
	if not key:
		raise ValueError("No API key provided.")
	if not key.startswith("gsk_"):
		raise ValueError("Invalid key format. Groq keys should start with gsk_.")
	return key


def chat_completion(api_key: str, messages: list[dict]) -> str:
	payload = {
		"model": MODEL_NAME,
		"messages": messages,
		"temperature": 0.7,
	}

	body = json.dumps(payload).encode("utf-8")
	request = urllib.request.Request(
		GROQ_API_URL,
		data=body,
		headers={
			"Authorization": f"Bearer {api_key}",
			"Content-Type": "application/json",
			"Accept": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Python-Groq-Client/1.0",
		},
		method="POST",
	)

	try:
		with urllib.request.urlopen(request, timeout=120) as response:
			response_data = json.loads(response.read().decode("utf-8"))
	except urllib.error.HTTPError as http_error:
		error_text = http_error.read().decode("utf-8", errors="replace")
		if "error code: 1010" in error_text.lower() or "access denied" in error_text.lower():
			raise RuntimeError(
				"HTTP 403 (Cloudflare 1010 Access Denied). This is usually network/IP/WAF blocking. "
				"Try a different network (mobile hotspot/VPN), verify your key on Groq Console, "
				"and ensure your region is supported."
			) from http_error
		raise RuntimeError(f"HTTP {http_error.code}: {error_text}") from http_error
	except urllib.error.URLError as url_error:
		raise RuntimeError(f"Network error: {url_error}") from url_error

	try:
		return response_data["choices"][0]["message"]["content"].strip()
	except (KeyError, IndexError, AttributeError) as parse_error:
		raise RuntimeError(f"Unexpected API response: {response_data}") from parse_error


def main() -> None:
	print("=" * 60)
	print("Groq Terminal Chatbot")
	print(f"Model: {MODEL_NAME}")
	print("Type 'exit' to quit.")
	print("=" * 60)

	try:
		api_key = get_api_key()
	except ValueError as error:
		print(f"Error: {error}")
		sys.exit(1)

	while True:
		user_text = input("\nYou: ").strip()
		if not user_text:
			continue
		if user_text.lower() in {"exit", "quit", "bye"}:
			print("Bot: Goodbye!")
			break

		try:
			assistant_text = chat_completion(api_key, [{"role": "user", "content": user_text}])
		except Exception as error:  # noqa: BLE001
			print(f"Bot error: {error}")
			continue
		print(f"Bot: {assistant_text}")


if __name__ == "__main__":
	main()