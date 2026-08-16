import os
from dotenv import load_dotenv
load_dotenv('env.env', override=True)

keys = [
    ('KEY_1', os.getenv('GEMINI_API_KEY')),
    ('KEY_2', os.getenv('GEMINI_API_KEY_2')),
    ('KEY_3', os.getenv('GEMINI_API_KEY_3')),
    ('KEY_4', os.getenv('GEMINI_API_KEY_4')),
]

from google import genai

for name, key in keys:
    if not key:
        print(f'{name}: NOT SET')
        continue
    print(f'\n--- Testing {name}: {key[:8]}...{key[-4:]} ---')
    try:
        client = genai.Client(api_key=key)
        r = client.models.generate_content(model='gemini-2.0-flash-lite', contents='Say OK')
        print(f'  SUCCESS: {r.text[:50]}')
    except Exception as e:
        err = str(e)
        if '429' in err:
            # Extract more details
            if 'limit: 0' in err:
                print(f'  QUOTA EXHAUSTED (limit: 0) - Free tier may be DISABLED on this project')
            else:
                print(f'  RATE LIMITED - Try again later')
        elif '400' in err:
            print(f'  BAD REQUEST - Check API key format')
        elif '403' in err:
            print(f'  PERMISSION DENIED - Key may have API restrictions')
        elif '401' in err:
            print(f'  UNAUTHORIZED - Invalid API key')
        else:
            print(f'  ERROR: {err[:300]}')
