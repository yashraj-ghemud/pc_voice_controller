import re
import os
import tempfile

import mic
import stt


def extract_number_from_speech(text: str):
    """pehla/first/1/one->1 | doosra/second/2/two->2 (Hindi+English)"""
    if not text:
        return None

    t = text.lower().strip()

    mapping = {
        1: ["1", "one", "first", "pehla", "pehli", "पहला", "पहली"],
        2: ["2", "two", "second", "doosra", "dusra", "दूसरा"],
        3: ["3", "three", "third", "teesra", "तीसरा"],
        4: ["4", "four", "fourth", "chautha", "चौथा"],
        5: ["5", "five", "fifth", "paanchwa", "पांचवा"],
    }

    m = re.search(r"\b(\d+)\b", t)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    for num, aliases in mapping.items():
        if any(a in t for a in aliases):
            return num
    return None


def listen_once() -> str:
    """Record one short utterance using existing project mic/stt stack."""
    audio_file = mic.record_audio()
    if not audio_file or not os.path.exists(audio_file):
        return ""
    text, _err = stt.transcribe_wav_google(audio_file)
    try:
        os.remove(audio_file)
    except OSError:
        pass
    return (text or "").strip()
