try:
    import google.genai
    print("✅ google-genai installed")
except ImportError:
    print("❌ google-genai MISSING")

try:
    import pyaudio
    print("✅ pyaudio installed")
except ImportError:
    print("❌ pyaudio MISSING")

try:
    import PIL
    print("✅ pillow installed")
except ImportError:
    print("❌ pillow MISSING")

try:
    import pygame
    print("✅ pygame installed")
except ImportError:
    print("❌ pygame MISSING")
