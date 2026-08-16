import asyncio
import edge_tts
from playsound import playsound

async def main():
    text = "अरे... सुनो। मैं तुम्हारे लिए कर देता हूँ। हो गया।"
    voice = "hi-IN-SwaraNeural"  
    rate = "+35%"
    pitch = "+0Hz"        # slightly brighter

    tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await tts.save("voice.mp3")
    playsound("voice.mp3")

asyncio.run(main())
