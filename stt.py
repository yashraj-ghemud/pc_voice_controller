import speech_recognition as sr


def transcribe_wav_google(audio_path: str, language: str = "en-IN") -> tuple[str | None, str | None]:
    """Transcribe a WAV file using Google's online Web Speech API.

    Returns:
        (text, error)
    """
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language=language)
        return text, None

    except sr.UnknownValueError:
        return None, "Speech was not clear enough to transcribe."
    except sr.RequestError as e:
        return None, f"Speech recognition request failed: {e}"
    except Exception as e:
        return None, f"Speech recognition error: {e}"
