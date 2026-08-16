import os
from dotenv import load_dotenv

print("--- Debugging API Key ---")

# 1. Check raw env var
raw_key = os.getenv("GROQ_API_KEY")
print(f"1. Initial GROQ_API_KEY: {raw_key[:10]}..." if raw_key else "1. Initial GROQ_API_KEY: None")

# 2. Load from file (standard)
load_dotenv("env.env")
file_key = os.getenv("GROQ_API_KEY")
print(f"2. After load_dotenv('env.env'): {file_key[:10]}..." if file_key else "2. After load_dotenv: None")

# 3. Load from file (override)
load_dotenv("env.env", override=True)
override_key = os.getenv("GROQ_API_KEY")
print(f"3. After load_dotenv(override=True): {override_key[:10]}..." if override_key else "3. After override: None")

if override_key:
    print("\n✅ Key found in env.env")
    if override_key.startswith("gsk_"):
        print("✅ Format looks correct (starts with gsk_)")
    else:
        print("❌ Format looks suspicious (should start with gsk_)")
else:
    print("\n❌ Key NOT found in env.env")
