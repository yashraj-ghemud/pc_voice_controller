import os
from google import genai
from dotenv import load_dotenv

# Load env
load_dotenv("env.env", override=True)
api_key = os.getenv("GEMINI_API_KEY")

print(f"Checking Key: {api_key[:5]}...{api_key[-3:]}")

try:
    client = genai.Client(api_key=api_key)
    print("Attempting to connect to Gemini 2.0 Flash...")
    response = client.models.generate_content(model="gemini-2.0-flash", contents="Say 'System Online'")
    print(f"✅ Success! Response: {response.text}")
except Exception as e:
    print(f"❌ Verification Failed: {e}")
