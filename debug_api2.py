import os
from dotenv import load_dotenv
load_dotenv('env.env', override=True)

from google import genai

key = os.getenv('GEMINI_API_KEY')
print(f"Testing key: {key[:10]}...")

client = genai.Client(api_key=key)

# Check if we can at least list models (doesn't consume quota)
print("\n1. Listing models (no quota needed)...")
try:
    models = list(client.models.list())
    print(f"   Found {len(models)} models - API KEY IS VALID!")
    print(f"   Sample models: {[m.name.split('/')[-1] for m in models[:5]]}")
except Exception as e:
    print(f"   ERROR listing models: {e}")

# Try a different model
print("\n2. Testing different models...")
test_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']

for model in test_models:
    try:
        r = client.models.generate_content(model=model, contents='Say hi')
        print(f"   {model}: SUCCESS - {r.text[:30]}")
        break
    except Exception as e:
        err_str = str(e)
        if 'limit: 0' in err_str:
            print(f"   {model}: limit: 0 (free tier disabled)")
        elif '429' in err_str:
            print(f"   {model}: Rate limited")
        elif '404' in err_str:
            print(f"   {model}: Model not found")
        else:
            print(f"   {model}: {err_str[:100]}")
