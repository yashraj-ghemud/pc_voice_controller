"""
voice.py - Inworld AI Text-to-Speech module.
Converts text to speech using the cloned voice "rrr" and plays it.
"""

import os
import base64
import tempfile
import requests
import pygame
import time
import uuid
import config


class InworldVoice:
    """Text-to-Speech using Inworld AI with cloned voice."""

    def __init__(self):
        if not config.INWORLD_API_KEY:
            raise RuntimeError("[ERROR] No Inworld API key found in .env!")

        self.url = config.INWORLD_TTS_URL
        self.headers = {
            "Authorization": f"Basic {config.INWORLD_API_KEY}",
            "Content-Type": "application/json",
        }
        self.voice_id = config.INWORLD_VOICE_ID
        self.model_id = config.INWORLD_MODEL_ID

        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        print(f"  [VOICE] Loaded: {self.voice_id}")

    def _split_text(self, text, max_chars=500):
        """Split long text into chunks at sentence boundaries."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        current = ""
        sentences = text.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|")

        for sentence in sentences:
            if len(current) + len(sentence) <= max_chars:
                current += sentence + " "
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = sentence + " "

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text]

    def speak(self, text):
        """
        Convert text to speech and play it aloud.
        Handles long text by splitting into chunks.
        """
        if not text or not text.strip():
            return

        chunks = self._split_text(text)

        for i, chunk in enumerate(chunks):
            try:
                payload = {
                    "text": chunk,
                    "voiceId": self.voice_id,
                    "modelId": self.model_id,
                    "talkingSpeed": 1.5,
                    "timestampType": "WORD",
                }

                response = requests.post(
                    self.url, json=payload, headers=self.headers, timeout=30
                )
                response.raise_for_status()

                result = response.json()
                audio_content = base64.b64decode(result["audioContent"])

                # Save to a unique temp file to avoid permission/locking issues
                unique_filename = f"nova_voice_{uuid.uuid4().hex}.mp3"
                temp_path = os.path.join(tempfile.gettempdir(), unique_filename)
                
                with open(temp_path, "wb") as f:
                    f.write(audio_content)

                self._play_audio(temp_path)

                # Cleanup
                try:
                    # Windows specific: sometimes file is still "busy" for a split second
                    time.sleep(0.1) 
                    os.remove(temp_path)
                except OSError:
                    pass

            except requests.exceptions.HTTPError as e:
                print(f"  [TTS ERROR] API error: {e}")
                if e.response is not None:
                    print(f"     Response: {e.response.text}")
            except Exception as e:
                print(f"  [VOICE ERROR] {e}")

    def _play_audio(self, file_path):
        """Play an audio file and wait for it to finish."""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Explicitly unload to release the file lock
            pygame.mixer.music.unload()

        except Exception as e:
            print(f"  [PLAYBACK ERROR] {e}")

    def cleanup(self):
        """Clean up pygame resources."""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
