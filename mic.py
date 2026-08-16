import pyaudio
import wave
import os
import speech_recognition as sr

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
OUTPUT_FILENAME = "input.wav"


def listen_voice(timeout=8, phrase_time_limit=10):
    """
    Listen for voice input using speech_recognition's built-in VAD.
    Automatically starts when speech is detected and stops when silence is detected.
    
    Returns:
        (audio_file_path, None) on success
        (None, error_string) on failure
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Sensitivity for ambient noise
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.5  # Seconds of silence before considering speech done

    try:
        with sr.Microphone(sample_rate=RATE) as source:
            print("🎤 Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🟢 Listening... (speak now)")

            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("✅ Voice captured!")
            except sr.WaitTimeoutError:
                return None, "timeout"

        # Save the captured audio to WAV file
        wav_data = audio.get_wav_data(convert_rate=RATE, convert_width=2)
        with open(OUTPUT_FILENAME, "wb") as f:
            f.write(wav_data)

        return OUTPUT_FILENAME, None

    except Exception as e:
        print(f"❌ Mic error: {e}")
        return None, str(e)


def record_audio(output_filename=OUTPUT_FILENAME, record_seconds=RECORD_SECONDS):
    """
    Fallback: Records audio for a fixed duration from the default microphone.
    """
    p = pyaudio.PyAudio()

    print(f"🎤 Listening... (Recording for {record_seconds}s)")
    
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        frames = []

        for i in range(0, int(RATE / CHUNK * record_seconds)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("✅ Recording finished.")

        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        return output_filename

    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        return None

if __name__ == "__main__":
    path, err = listen_voice()
    if path:
        print(f"Audio saved to: {path}")
    else:
        print(f"Error: {err}")
