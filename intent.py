"""
intent.py — Offline intent classifier for common PC commands.
Handles small tasks locally (no Gemini API call needed).
Returns None if intent is not recognized → falls through to Gemini.
"""

import re
import random

# ═══════════════════════════════════════════════════════════════════════════════
#  PRE-WRITTEN HINDI RESPONSES (multiple variations per action for natural feel)
# ═══════════════════════════════════════════════════════════════════════════════

RESPONSES = {
    # --- Volume ---
    "VOLUME_UP": [
        "वॉल्यूम बढ़ा दिया बाबू!",
        "लो जी, आवाज़ बढ़ा दी।",
        "वॉल्यूम ऊपर कर दिया, अब सुनाई दे रहा है ना?",
        "आवाज़ तेज़ कर दी, और बढ़ाऊँ?",
        "बस ये लो, वॉल्यूम बढ़ गया!",
        "हाँ जी, आवाज़ बढ़ा रही हूँ।",
        "ओके, वॉल्यूम अप कर दिया!",
    ],
    "VOLUME_DOWN": [
        "वॉल्यूम कम कर दिया।",
        "आवाज़ थोड़ी कम कर दी।",
        "लो जी, धीमा कर दिया।",
        "वॉल्यूम डाउन कर दिया, ठीक है ना?",
        "हाँ, आवाज़ कम कर रही हूँ।",
        "ओके, वॉल्यूम नीचे किया!",
    ],
    "SET_VOLUME": [
        "वॉल्यूम {value} परसेंट पे सेट कर दिया!",
        "लो जी, आवाज़ {value}% कर दी।",
        "हाँ बोलो, वॉल्यूम {value} पर लगा दिया।",
        "ओके डन, वॉल्यूम अब {value}% है।",
        "बस जी, {value} परसेंट पे सेट है अब।",
        "वॉल्यूम {value}% किया, और कुछ?",
    ],
    "MUTE": [
        "म्यूट कर दिया, शांति!",
        "चुप कर दिया सब कुछ।",
        "ओके, आवाज़ बंद कर दी।",
        "म्यूट हो गया, अब सन्नाटा है।",
        "लो जी, साउंड ऑफ कर दिया।",
        "हाँ बाबू, म्यूट कर दिया।",
    ],
    "UNMUTE": [
        "अनम्यूट कर दिया!",
        "आवाज़ वापस आ गई!",
        "लो जी, साउंड ऑन कर दिया।",
        "म्यूट हटा दिया, अब सुनो।",
        "ओके, आवाज़ चालू कर दी।",
    ],

    # --- Brightness ---
    "BRIGHTNESS_UP": [
        "ब्राइटनेस बढ़ा दी!",
        "स्क्रीन और तेज़ कर दी।",
        "लो जी, रोशनी बढ़ा दी।",
        "ब्राइटनेस ऊपर कर दी, दिख रहा है ना?",
        "हाँ, और चमकदार कर दी स्क्रीन।",
    ],
    "BRIGHTNESS_DOWN": [
        "ब्राइटनेस कम कर दी।",
        "स्क्रीन थोड़ी डिम कर दी।",
        "लो जी, रोशनी कम कर दी।",
        "ब्राइटनेस डाउन कर दी, आँखों को आराम।",
        "हाँ, धीमी कर दी स्क्रीन।",
    ],
    "SET_BRIGHTNESS": [
        "ब्राइटनेस {value}% कर दी!",
        "लो जी, स्क्रीन {value} परसेंट पे सेट है।",
        "ब्राइटनेस {value}% पर लगा दी।",
        "ओके, {value}% ब्राइटनेस सेट है अब।",
    ],

    # --- WiFi ---
    "WIFI_ON": [
        "वाईफाई ऑन कर दिया!",
        "लो जी, वाईफाई चालू है अब।",
        "वाईफाई कनेक्ट कर रही हूँ।",
        "हाँ बाबू, वाईफाई ऑन कर दिया।",
        "ओके, इंटरनेट चालू कर दिया।",
    ],
    "WIFI_OFF": [
        "वाईफाई ऑफ कर दिया।",
        "इंटरनेट बंद कर दिया।",
        "लो जी, वाईफाई डिसकनेक्ट कर दिया।",
        "ओके, वाईफाई बंद है अब।",
        "हाँ, वाईफाई ऑफ कर रही हूँ।",
    ],

    # --- Bluetooth ---
    "BLUETOOTH_ON": [
        "ब्लूटूथ ऑन कर दिया!",
        "लो जी, ब्लूटूथ चालू है।",
        "हाँ बाबू, ब्लूटूथ ऑन कर दिया।",
        "ब्लूटूथ कनेक्शन चालू कर दिया।",
    ],
    "BLUETOOTH_OFF": [
        "ब्लूटूथ ऑफ कर दिया।",
        "लो जी, ब्लूटूथ बंद कर दिया।",
        "ओके, ब्लूटूथ डिसकनेक्ट कर दिया।",
        "हाँ, ब्लूटूथ बंद है अब।",
    ],

    # --- Screenshot ---
    "SCREENSHOT": [
        "स्क्रीनशॉट ले लिया!",
        "लो जी, फोटो खींच ली स्क्रीन की।",
        "स्क्रीनशॉट सेव हो गया!",
        "हाँ बाबू, स्क्रीन कैप्चर कर लिया।",
        "ओके, स्क्रीनशॉट ले लिया है।",
    ],

    # --- System ---
    "SHUTDOWN": [
        "ओके, सिस्टम बंद कर रही हूँ। बाय बाय!",
        "शटडाउन कर रही हूँ, मिलते हैं फिर!",
        "कंप्यूटर बंद हो रहा है, टेक केयर!",
    ],
    "RESTART": [
        "रीस्टार्ट कर रही हूँ, थोड़ी देर रुको।",
        "सिस्टम रीस्टार्ट हो रहा है!",
        "ओके, रीबूट कर रही हूँ।",
    ],
    "SLEEP": [
        "कंप्यूटर को सुला रही हूँ, गुड नाइट!",
        "स्लीप मोड में डाल रही हूँ।",
        "ओके, सिस्टम सो रहा है अब।",
    ],
    "LOCK": [
        "स्क्रीन लॉक कर दी!",
        "लो जी, पीसी लॉक है अब।",
        "लॉक कर दिया, सेफ है अब।",
        "ओके, स्क्रीन लॉक कर दी।",
    ],

    # --- Open/Close App ---
    "OPEN_APP": [
        "{target} खोल रही हूँ!",
        "लो जी, {target} ओपन कर रही हूँ।",
        "हाँ बाबू, {target} चालू कर रही हूँ।",
        "ओके, {target} खोलती हूँ।",
        "{target} स्टार्ट कर रही हूँ, रुको ज़रा।",
    ],
    "CLOSE_APP": [
        "{target} बंद कर दिया!",
        "लो जी, {target} क्लोज़ कर दिया।",
        "ओके, {target} बंद कर रही हूँ।",
        "{target} बंद है अब।",
    ],

    # --- Search ---
    "SEARCH_WEB": [
        "{value} सर्च कर रही हूँ!",
        "लो जी, गूगल पे {value} ढूँढ रही हूँ।",
        "ओके, {value} सर्च करती हूँ।",
        "हाँ, {value} खोज रही हूँ इंटरनेट पे।",
    ],

    # --- Desktop Switch ---
    "SWITCH_DESKTOP_LEFT": [
        "लेफ्ट डेस्कटॉप पे जा रही हूँ!",
        "ओके, बाएं डेस्कटॉप पे स्विच कर रही हूँ।",
        "हाँ, दूसरे डेस्कटॉप पे जा रही हूँ।",
        "लेफ्ट साइड का डेस्कटॉप खोल रही हूँ।",
    ],
    "SWITCH_DESKTOP_RIGHT": [
        "राइट डेस्कटॉप पे वापस आ रही हूँ!",
        "ओके, दाएं डेस्कटॉप पे स्विच कर रही हूँ।",
        "वापस आ गई मैन डेस्कटॉप पे!",
        "राइट साइड का डेस्कटॉप खोल रही हूँ।",
    ],

    # --- Media ---
    "PLAY_MEDIA": [
        "गाना चालू कर दिया!",
        "लो जी, म्यूज़िक प्ले कर रही हूँ।",
        "ओके, सॉन्ग बजा रही हूँ!",
        "हाँ, गाना शुरू कर दिया।",
        "म्यूज़िक प्ले कर दिया!",
    ],
    "PAUSE_MEDIA": [
        "गाना रोक दिया!",
        "लो जी, म्यूज़िक पॉज़ कर दिया।",
        "ओके, सॉन्ग रुक गया।",
        "हाँ, गाना रोक दिया अभी।",
    ],
    "STOP_MEDIA": [
        "म्यूज़िक बंद कर दिया!",
        "गाना स्टॉप कर दिया।",
        "ओके, म्यूज़िक बंद है अब।",
    ],
    "NEXT_TRACK": [
        "अगला गाना लगा दिया!",
        "नेक्स्ट ट्रैक पे जा रही हूँ।",
        "ओके, अगला सॉन्ग चालू!",
    ],
    "PREV_TRACK": [
        "पिछला गाना लगा दिया!",
        "प्रीवियस ट्रैक पे जा रही हूँ।",
        "ओके, पहले वाला सॉन्ग!",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
#  INTENT PATTERNS (English + Hindi + Hinglish — lots of variations)
# ═══════════════════════════════════════════════════════════════════════════════

def _p(patterns):
    """Compile a list of regex patterns (case-insensitive)."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]

# Each entry: (compiled_patterns, action_name, extract_func_or_None)
# extract_func takes match object and returns (target, value)

INTENTS = []

# ─── Volume Up ────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(volume|vol|sound|awaz|awaaz|aawaz|आवाज़?|वॉल्यूम|साउंड)\b.*(up|increase|badha|badhao|upar|uper|tez|tej|zyada|jyada|बढ़ा|ऊपर|तेज़?|ज़्यादा)",
    r"\b(badha|badhao|tez|tej)\b.*(volume|vol|sound|awaz|awaaz|आवाज़?|वॉल्यूम)",
    r"\b(volume|vol)\s*(up|badha|badhao)\b",
    r"\b(awaaz|awaz|aawaz)\s*(badha|badhao|tez|zyada)\b",
    r"\blouder\b",
    r"\bturn\s*(it\s*)?up\b",
    r"\braise\s*(the\s*)?(volume|sound)\b",
    r"\bआवाज़?\s*(बढ़ा|तेज़?)\b",
    r"\bवॉल्यूम\s*(बढ़ा|अप|ऊपर)\b",
]), "VOLUME_UP", None))

# ─── Volume Down ──────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(volume|vol|sound|awaz|awaaz|aawaz|आवाज़?|वॉल्यूम|साउंड)\b.*(down|decrease|kam|dhima|dhime|niche|neeche|कम|नीचे|धीमा|धीमे)",
    r"\b(kam|dhima|dhime)\b.*(volume|vol|sound|awaz|awaaz|आवाज़?|वॉल्यूम)",
    r"\b(volume|vol)\s*(down|kam|dhima)\b",
    r"\b(awaaz|awaz|aawaz)\s*(kam|dhima|dhime|halka)\b",
    r"\bquieter\b",
    r"\bturn\s*(it\s*)?down\b",
    r"\blower\s*(the\s*)?(volume|sound)\b",
    r"\bआवाज़?\s*(कम|धीम[ाेी])\b",
    r"\bवॉल्यूम\s*(कम|डाउन|नीचे)\b",
]), "VOLUME_DOWN", None))

# ─── Set Volume (with number) ────────────────────────────────────────────────
def _extract_volume(text):
    m = re.search(r'(\d+)\s*(%|percent|परसेंट)?', text)
    if m:
        return None, int(m.group(1))
    return None, 50

INTENTS.append((_p([
    r"\b(volume|vol|sound|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*\b(\d+)\s*(%|percent|परसेंट)?\b",
    r"\b(set|change|kar|rakh|rakho|सेट|रख)\b.*(volume|vol|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*\b(\d+)",
    r"\b(\d+)\s*(%|percent|परसेंट)?\s*(volume|vol|awaz|awaaz|आवाज़?|वॉल्यूम)\b",
    r"\bवॉल्यूम\s*(\d+)\b",
    r"\bआवाज़?\s*(\d+)\b",
    r"\b(volume|vol)\s+(\d+)\b",
]), "SET_VOLUME", _extract_volume))

# ─── Mute ─────────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(mute|silent|shant|chup|शांत|म्यूट|चुप|बंद\s*कर.*आवाज़?)\b",
    r"\b(sound|volume|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*(off|band|बंद|mute)\b",
    r"\b(band|बंद)\b.*(sound|awaz|awaaz|आवाज़?|volume)\b",
    r"\bsilence\b",
    r"\bshut\s*up\b",
    r"\bआवाज़?\s*(बंद|ऑफ)\b",
]), "MUTE", None))

# ─── Unmute ───────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(unmute|अनम्यूट)\b",
    r"\b(sound|volume|awaz|awaaz|आवाज़?|वॉल्यूम)\b.*(on|chalu|shuru|चालू)\b",
    r"\b(chalu|shuru|चालू)\b.*(sound|awaz|awaaz|आवाज़?|volume)\b",
    r"\bआवाज़?\s*(चालू|ऑन)\b",
]), "UNMUTE", None))

# ─── Brightness Up ────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|चमक|रोशनी|ब्राइटनेस)\b.*(up|increase|badha|badhao|tez|बढ़ा|तेज़?|ज़्यादा|zyada)",
    r"\b(badha|badhao|tez)\b.*(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|रोशनी|ब्राइटनेस)",
    r"\bbrighter\b",
    r"\bरोशनी\s*(बढ़ा|तेज़?)\b",
    r"\bब्राइटनेस\s*(बढ़ा|अप|ऊपर)\b",
]), "BRIGHTNESS_UP", None))

# ─── Brightness Down ──────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|चमक|रोशनी|ब्राइटनेस)\b.*(down|decrease|kam|dhima|कम|धीमा|नीचे)",
    r"\b(kam|dhima)\b.*(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|रोशनी|ब्राइटनेस)",
    r"\bdimmer?\b",
    r"\bdim\s*(the\s*)?(screen|light)\b",
    r"\bरोशनी\s*(कम|धीमी)\b",
    r"\bब्राइटनेस\s*(कम|डाउन)\b",
]), "BRIGHTNESS_DOWN", None))

# ─── Set Brightness (with number) ────────────────────────────────────────────
def _extract_brightness(text):
    m = re.search(r'(\d+)\s*(%|percent|परसेंट)?', text)
    if m:
        return None, int(m.group(1))
    return None, 50

INTENTS.append((_p([
    r"\b(brightness|bright|brighness|brightnes|brigthness|roshni|chamak|ब्राइटनेस|रोशनी)\b.*\b(\d+)\s*(%|percent|परसेंट)?\b",
    r"\b(set|change|kar|rakh)\b.*(brightness|bright|brighness|brightnes|brigthness|roshni|ब्राइटनेस|रोशनी)\b.*\b(\d+)",
    r"\b(\d+)\s*(%|percent)?\s*(brightness|bright|brighness|brightnes|brigthness)\b",
    r"\bब्राइटनेस\s*(\d+)\b",
]), "SET_BRIGHTNESS", _extract_brightness))

# ─── WiFi On ──────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(wifi|wi-fi|वाईफाई|वाई\s*फाई|internet|इंटरनेट)\b.*(on|chalu|enable|start|connect|jodo|चालू|ऑन|कनेक्ट)",
    r"\b(chalu|on|enable|start|connect|चालू|ऑन)\b.*(wifi|wi-fi|वाईफाई|internet|इंटरनेट)\b",
    r"\bturn\s*on\s*(the\s*)?(wifi|wi-fi|internet)\b",
    r"\b(wifi|wi-fi)\s*(on|chalu|चालू)\b",
    r"\bवाईफाई\s*(चालू|ऑन|कनेक्ट)\b",
    r"\bइंटरनेट\s*(चालू|ऑन)\b",
    r"\bnet\s*(on|chalu|chalao)\b",
]), "WIFI_ON", None))

# ─── WiFi Off ─────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(wifi|wi-fi|वाईफाई|वाई\s*फाई|internet|इंटरनेट)\b.*(off|band|disable|stop|disconnect|हटा|बंद|ऑफ|डिसकनेक्ट)",
    r"\b(band|off|disable|stop|disconnect|बंद|ऑफ)\b.*(wifi|wi-fi|वाईफाई|internet|इंटरनेट)\b",
    r"\bturn\s*off\s*(the\s*)?(wifi|wi-fi|internet)\b",
    r"\b(wifi|wi-fi)\s*(off|band|बंद)\b",
    r"\bवाईफाई\s*(बंद|ऑफ|डिसकनेक्ट)\b",
    r"\bइंटरनेट\s*(बंद|ऑफ)\b",
    r"\bnet\s*(off|band|bandh)\b",
]), "WIFI_OFF", None))

# ─── Bluetooth On ─────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(bluetooth|bt|ब्लूटूथ|ब्लूटूस)\b.*(on|chalu|enable|start|connect|चालू|ऑन|कनेक्ट)",
    r"\b(chalu|on|enable|start|चालू|ऑन)\b.*(bluetooth|bt|ब्लूटूथ)\b",
    r"\bturn\s*on\s*(the\s*)?(bluetooth|bt)\b",
    r"\b(bluetooth|bt)\s*(on|chalu|चालू)\b",
    r"\bब्लूटूथ\s*(चालू|ऑन)\b",
]), "BLUETOOTH_ON", None))

# ─── Bluetooth Off ────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(bluetooth|bt|ब्लूटूथ|ब्लूटूस)\b.*(off|band|disable|stop|disconnect|बंद|ऑफ)",
    r"\b(band|off|disable|stop|disconnect|बंद|ऑफ)\b.*(bluetooth|bt|ब्लूटूथ)\b",
    r"\bturn\s*off\s*(the\s*)?(bluetooth|bt)\b",
    r"\b(bluetooth|bt)\s*(off|band|बंद)\b",
    r"\bब्लूटूथ\s*(बंद|ऑफ)\b",
]), "BLUETOOTH_OFF", None))

# ─── Screenshot ───────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(screenshot|screen\s*shot|ss|स्क्रीनशॉट|स्क्रीन\s*शॉट)\b",
    r"\b(capture|कैप्चर)\s*(screen|स्क्रीन)\b",
    r"\b(photo|फोटो)\s*(screen|स्क्रीन|le|lo|ले|लो)\b",
    r"\bscreen\s*(capture|photo|pic)\b",
    r"\btak\s*a?\s*(screenshot|ss|pic)\b",
    r"\bस्क्रीन\s*(की\s*)?(फोटो|तस्वीर)\b",
]), "SCREENSHOT", None))

# ─── Shutdown ─────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(shutdown|shut\s*down|power\s*off|शटडाउन|बंद\s*कर\s*(दो|दे|do)?(\s*कंप्यूटर)?)\b",
    r"\b(computer|pc|system|कंप्यूटर|पीसी|सिस्टम)\b.*(band|off|shutdown|बंद)\b",
    r"\b(band|बंद)\b.*(computer|pc|system|कंप्यूटर|पीसी)\b",
    r"\bpower\s*off\b",
    r"\bपावर\s*ऑफ\b",
]), "SHUTDOWN", None))

# ─── Restart ──────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(restart|reboot|रीस्टार्ट|रीबूट)\b",
    r"\b(computer|pc|system|कंप्यूटर|पीसी)\b.*(restart|reboot|रीस्टार्ट)\b",
    r"\bdubara\s*chalu\b",
    r"\bदुबारा\s*चालू\b",
]), "RESTART", None))

# ─── Sleep ────────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(sleep|hibernate|sone\s*do|sula\s*do|स्लीप|सोने\s*दो|सुला\s*दो)\b",
    r"\b(computer|pc|system|कंप्यूटर|पीसी)\b.*(sleep|sone|sula|स्लीप|सो)\b",
    r"\bhibernate\b",
]), "SLEEP", None))

# ─── Lock ─────────────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(lock|screen\s*lock|लॉक)\b",
    r"\b(computer|pc|screen|स्क्रीन|कंप्यूटर|पीसी)\b.*(lock|लॉक)\b",
    r"\b(lock|लॉक)\b.*(computer|pc|screen|स्क्रीन|कंप्यूटर)\b",
    r"\bस्क्रीन\s*लॉक\b",
]), "LOCK", None))

# ─── Common Cleaner Helper ────────────────────────────────────────────────────
def _clean_target(text):
    """Strip common filler words from the extracted target."""
    if not text: return text
    # Remove common conversational fillers
    fillers = [r'\bplease\b', r'\bpls\b', r'\bplz\b', r'\bkholdo\b', r'\bkhol\s*do\b', 
               r'\bkar\s*do\b', r'\byar\b', r'\byaar\b', r'\bbro\b', r'\bbhai\b', 
               r'\bbabu\b', r'\bjaldi\b']
    
    clean = text
    for f in fillers:
        clean = re.sub(f, '', clean, flags=re.IGNORECASE)
    
    # Remove trailing punctuation
    clean = re.sub(r'[!.,]+$', '', clean)
    return clean.strip()


# ─── Switch Desktop Left ─────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(left|baye[mn]?|बाए[ंम]?|लेफ्ट)\s+(desktop|screen|डेस्कटॉप|स्क्रीन)",
    r"\b(desktop|डेस्कटॉप)\s+(left|baye[mn]?|बाए[ंम]?|लेफ्ट)",
    r"\b(left|baye[mn]?|बाए[ंम]?|लेफ्ट)\b.*(ja|jao|switch|chale?\s*ja|जा|जाओ|स्विच)",
    r"\b(switch|ja|jao|जा|chale?\s*ja)\b.*(left|baye[mn]?|बाए[ंम]?|लेफ्ट)\s*(desktop|डेस्कटॉप|side|साइड)?",
    r"\bleft\s*desktop\s*(mai|me|mein|में|pe|par|पे|पर)?\s*(ja|jao|switch|जा|जाओ)?\b",
    r"\bdoosre?\s*desktop\b",
    r"\bdusre?\s*desktop\b",
]), "SWITCH_DESKTOP_LEFT", None))

# ─── Switch Desktop Right ────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(right|daye[mn]?|दाए[ंम]?|राइट)\s+(desktop|screen|डेस्कटॉप|स्क्रीन)",
    r"\b(desktop|डेस्कटॉप)\s+(right|daye[mn]?|दाए[ंम]?|राइट)",
    r"\b(right|daye[mn]?|दाए[ंम]?|राइट)\b.*(ja|jao|switch|chale?\s*ja|जा|जाओ|स्विच)",
    r"\b(wapas|wapis|vapas|वापस|back)\s*(aa|aao|आ|आओ|ja|jao)\b",
    r"\b(main|original|pehle?\s*wala?)\s*(desktop|डेस्कटॉप)",
    r"\bright\s*desktop\s*(mai|me|mein|में|pe|par|पे|पर)?\s*(ja|jao|switch|जा|जाओ)?\b",
]), "SWITCH_DESKTOP_RIGHT", None))

# ─── Play Media ──────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(play|baja|bajao|chala|chalao|resume|प्ले|बजा|बजाओ|चला|चलाओ)\s*(song|music|gaana|gana|media|track|सॉन्ग|गाना|म्यूज़िक|म्यूजिक)?\b",
    r"\b(song|music|gaana|gana|सॉन्ग|गाना|म्यूज़िक|म्यूजिक)\s*(play|baja|bajao|chala|chalao|shuru|प्ले|बजा|चला|चलाओ|शुरू)\b",
    r"\b(song|gaana|gana|music|गाना|सॉन्ग|म्यूज़िक)\s*(kar|karo|kr|करो?)\b",
    r"\bplay\s*kr\b",
    r"\bgaana\s*(baja|chala|laga|शुरू)\b",
    r"\bmusic\s*(on|chalu|start|play)\b",
]), "PLAY_MEDIA", None))

# ─── Pause Media ─────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(pause|rok|roko|ruk|ruko|tham|thaam|पॉज़?|रोक|रोको|रुक|रुको|थाम)\s*(song|music|gaana|gana|media|सॉन्ग|गाना|म्यूज़िक)?\b",
    r"\b(song|music|gaana|gana|सॉन्ग|गाना|म्यूज़िक)\s*(pause|rok|roko|band|पॉज़?|रोक|रोको|बंद)\b",
    r"\b(gaana|gana|song|music|गाना)\s*(rok|roko|band\s*kar|रोक|बंद)\b",
]), "PAUSE_MEDIA", None))

# ─── Stop Media ──────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(stop|band)\s*(song|music|gaana|gana|media|सॉन्ग|गाना|म्यूज़िक)\b",
    r"\b(song|music|gaana|gana|सॉन्ग|गाना|म्यूज़िक)\s*(stop|band|बंद|स्टॉप)\s*(kar|karo|kr|करो?)?\b",
    r"\bmusic\s*(off|band|stop)\b",
]), "STOP_MEDIA", None))

# ─── Next Track ──────────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(next|agla|अगला|नेक्स्ट)\s*(song|track|gaana|gana|सॉन्ग|गाना|ट्रैक)?\b",
    r"\b(song|gaana|gana|track|सॉन्ग|गाना)\s*(skip|next|agla|अगला|नेक्स्ट|स्किप)\b",
    r"\bskip\s*(song|track|gaana)?\b",
]), "NEXT_TRACK", None))

# ─── Previous Track ──────────────────────────────────────────────────────────
INTENTS.append((_p([
    r"\b(prev|previous|pichla|पिछला|प्रीवियस)\s*(song|track|gaana|gana|सॉन्ग|गाना|ट्रैक)?\b",
    r"\b(song|gaana|gana|track|सॉन्ग|गाना)\s*(prev|previous|pichla|पिछला)\b",
    r"\bpehle\s*wala\s*(song|gaana|gana)?\b",
]), "PREV_TRACK", None))


# ─── Open App ─────────────────────────────────────────────────────────────────
def _extract_app_open(text):
    # Try to extract app name BEFORE or AFTER trigger words
    # After trigger: "open spotify", "khol do spotify"
    m1 = re.search(r'\b(?:open|launch|start|khol|chalao|chalu\s*kar|खोल|चालू\s*कर|ओपन|लॉन्च|स्टार्ट)\s+(.+)', text, re.IGNORECASE)
    if m1:
        return _clean_target(m1.group(1)), None
    
    # Before trigger: "spotify open", "spotify khol do"
    m2 = re.search(r'(.+?)\s+(?:open|khol|kholdo|khol\s*do|chalao|chalu|खोल|खोल\s*दो|चालू)', text, re.IGNORECASE)
    if m2:
        return _clean_target(m2.group(1)), None
        
    return _clean_target(text), None

INTENTS.append((_p([
    r"\b(open|launch|start|run)\s+\w+",
    r"\b(khol|kholdo|khol\s*do|chalao|chalu\s*kar|chalu\s*karo)\s+\w+",
    r"\b(खोल|खोल\s*दो|चालू\s*कर|चालू\s*करो|ओपन|लॉन्च|स्टार्ट)\s+\w+",
    r"\b\w+\s+(open|khol|kholdo|खोल|खोल\s*दो)\b",
    r"\b\w+\s+(chalu|chalao|चालू)\s*(kar|karo|करो?)?\b",
]), "OPEN_APP", _extract_app_open))

# ─── Close App ────────────────────────────────────────────────────────────────
def _extract_app_close(text):
    m1 = re.search(r'\b(?:close|exit|quit|kill|band\s*kar|hatao|बंद\s*कर|हटा|क्लोज़?)\s+(.+)', text, re.IGNORECASE)
    if m1:
        return _clean_target(m1.group(1)), None
        
    m2 = re.search(r'(.+?)\s+(?:band|close|बंद|hatao|hata\s*do|हटा|हटा\s*दो)', text, re.IGNORECASE)
    if m2:
        return _clean_target(m2.group(1)), None
        
    return _clean_target(text), None

INTENTS.append((_p([
    r"\b(close|exit|quit|kill|terminate)\s+\w+",
    r"\b(band\s*kar|band\s*karo|hatao|hata\s*do)\s+\w+",
    r"\b(बंद\s*कर|बंद\s*करो|हटा|हटा\s*दो|क्लोज़?)\s+\w+",
    r"\b\w+\s+(band|close|बंद)\s*(kar|karo|करो?)?\b",
]), "CLOSE_APP", _extract_app_close))

# ─── Search Web ───────────────────────────────────────────────────────────────
def _extract_search(text):
    m = re.search(r'\b(?:search|google|find|dhoond|dhundh|khoj|talaash|ढूँढ|खोज|सर्च|गूगल|तलाश)\s+(?:for|pe|par|पर|पे)?\s*(.+)', text, re.IGNORECASE)
    if m:
        return None, _clean_target(m.group(1))
    return None, _clean_target(text)

INTENTS.append((_p([
    r"\b(search|google|find|look\s*up)\s+.+",
    r"\b(dhoond|dhundh|khoj|talaash)\s+.+",
    r"\b(ढूँढ|खोज|सर्च|गूगल|तलाश)\s+.+",
    r"\b(search|google|सर्च|गूगल)\s+(for|pe|par|पर|पे)?\s*.+",
]), "SEARCH_WEB", _extract_search))


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN CLASSIFY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def classify(text):
    """
    Try to match the user's text to a known intent locally.

    Returns:
        dict: {"action": str, "target": str|None, "value": int|None, "say": str}
        None: if no match → should be sent to Gemini
    """
    if not text or not text.strip():
        return None

    text_clean = text.strip()

    # ── SET_VOLUME must be checked BEFORE generic VOLUME_UP/DOWN ──
    # because "volume 40" matches both, but SET_VOLUME is more specific
    for patterns, action, extractor in INTENTS:
        for pat in patterns:
            if pat.search(text_clean):
                target, value = (None, None)
                if extractor:
                    target, value = extractor(text_clean)

                # Get a random Hindi response
                say = random.choice(RESPONSES.get(action, ["ओके, कर दिया!"]))
                say = say.replace("{value}", str(value) if value else "").replace("{target}", str(target) if target else "")

                return {
                    "action": action,
                    "target": target,
                    "value": value,
                    "say": say,
                }

    return None  # Not recognized → send to Gemini


if __name__ == "__main__":
    # Quick test
    tests = [
        "volume up", "awaz badha", "वॉल्यूम बढ़ा",
        "volume 40", "set volume 75%",
        "mute", "chup kar", "unmute",
        "brightness up", "roshni kam kar",
        "wifi on", "bluetooth off",
        "open chrome", "chrome khol do",
        "close notepad", "notepad band kar",
        "screenshot", "स्क्रीनशॉट",
        "search python tutorial",
        "hello", "namaste", "shukriya",
        "shutdown", "restart", "lock",
    ]
    for t in tests:
        result = classify(t)
        if result:
            print(f"✅ '{t}' → {result['action']} | say: {result['say']}")
        else:
            print(f"❌ '{t}' → GEMINI")
