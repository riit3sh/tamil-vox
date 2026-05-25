import re
import random
import unicodedata
from typing import Optional

# ── 1. EMOTION DETECTION ──────────────────────────────────────────────────────

EMOTION_TAGS = [
    "shocked", "laughing", "outraged", "sighing",
    "whispering", "gossiping", "resigned", "surprised", "crying",
    "excited", "calm",
]

# Content-based signals — fallback when LLM forgets the [tag].
# Ordered by specificity: more unique signals first.
CONTENT_EMOTION_SIGNALS: dict[str, list[str]] = {
    "outraged":   ["அடப்பாவி", "over ah", "enna logic"],
    "laughing":   ["ஹா —", "ஹா ஹா", "சிரிப்பா"],
    "shocked":    ["என்னடா இது", "நம்பவே முடியல", "seriously-யா"],
    "sighing":    ["என்னமோ போ", "என்ன பண்றோம்"],
    "gossiping":  ["யாருக்கும் சொல்லாதே"],
    "whispering": ["யாருக்கும் சொல்லாதே", "தே தே"],
    "excited":    ["போலாமா", "கிளம்பலாம்", "வாசலா"],
    "resigned":   ["சரி சரி", "ஆகல் ஆகவே ஆகல்"],
    "calm":       ["நல்லா இருக்கேன்", "பரவாயில்ல", "ஓடுது life", "ஆமா ஆமா", "சரிதான்"],
}


def detect_emotion(text: str) -> str:
    """Detect emotion from [tag] or, as fallback, from content signals.

    The LLM occasionally skips the [emotion] tag. This two-pass detection
    means 'அடப்பாவி — ...' still resolves as outraged even without a tag.
    """
    lower = text.lower()
    # Pass 1: explicit [tag]
    for tag in EMOTION_TAGS:
        if f"[{tag}]" in lower:
            return tag
    # Pass 2: content signals (fallback)
    for emotion, signals in CONTENT_EMOTION_SIGNALS.items():
        for signal in signals:
            if signal in text:
                return emotion
    return "normal"


# ── 2. EMOTION → NATURAL ONSET / TAIL ────────────────────────────────────────

EMOTION_ONSETS = {
    "shocked":    "என்னடா இது —",
    "laughing":   "",           # no forced opener — let context drive it naturally
    "outraged":   "அடப்பாவி,",
    "sighing":    "",           # adds to END only
    "whispering": "",
    "gossiping":  "",           # conspiratorial — no showy opener
    "resigned":   "",
    "excited":    "ஆமா-ஆ? —",
    "calm":       "",           # no onset — calm is understated by definition
    "surprised":  "ஆமா-ஆ? —",
    "crying":     "ஐயய்யோ —",
    "normal":     "",
}

EMOTION_TAILS = {
    "sighing":    "...என்னமோ போ..........",
    "resigned":   "...என்ன பண்றோம்..........",
    "whispering": "...யாருக்கும் சொல்லாதே",
    "gossiping":  "...யாருக்கும் சொல்லாதே",
    "crying":     "...என்ன பண்றோம்..........",
}

# TTS pace per emotion — passed to Sarvam bulbul:v3.
# Updated prosody table: smoother and faster casual rhythm
EMOTION_PACE = {
    "calm": 0.96,
    "normal": 0.98,
    "sighing": 0.90,
    "playful": 1.00,
    "outraged": 1.03,
}

def convert_emotion_to_text(text: str, emotion: str) -> str:
    """Prepend natural onset and/or append natural tail based on emotion.

    Checks whether the onset / tail keywords already appear in the text
    before inserting them, preventing duplication when the LLM has already
    written its own opener or closer.
    """
    onset = EMOTION_ONSETS.get(emotion, "")
    tail  = EMOTION_TAILS.get(emotion, "")

    if onset:
        onset_check = onset.replace(" —", "").replace(",", "").strip()
        if onset_check not in text:
            text = onset + " " + text

    if tail:
        tail_check = tail.replace(".", "").strip()
        if tail_check not in text:
            text = text.rstrip(".") + " " + tail

    return text


# ── 3. REMOVE EMOTION TAGS ────────────────────────────────────────────────────

def remove_emotion_tags(text: str) -> str:
    """Strip all [emotion] tags from text."""
    return re.sub(r'\[.*?\]', '', text).strip()


# ── 4. FIX FORMAL TAMIL → COLLOQUIAL ─────────────────────────────────────────

FORMAL_TO_COLLOQUIAL = {

    # ── PRONOUNS ──────────────────────────────────────────────
    "அவர்கள்":          "அவங்க",
    "இவர்கள்":          "இவங்க",
    "அவர்":             "அவரு",
    "இவர்":             "இவரு",
    "நாங்கள்":          "நாங்க",
    "நீங்கள்":          "நீங்க",
    "உங்களுக்கு":       "உங்களுக்கு",
    "என்னுடைய":         "என்னோட",
    "உன்னுடைய":         "உன்னோட",

    # ── KINSHIP — map formal Tamil to natural Tanglish ────────
    "சகோதரி":           "sister",
    "சகோதரன்":          "brother",
    "நண்பன்":           "friend",
    "நண்பி":            "friend",
    "தாயார்":           "அம்மா",
    "தந்தையார்":        "அப்பா",
    "பாட்டி":           "பாட்டி",
    "தாத்தா":           "தாத்தா",
    "கணவர்":            "husband",
    "மனைவி":            "wife",
    "மகன்":             "son",
    "மகள்":             "daughter",

    # ── EMOTIONS / STATES — formal → natural ──────────────────
    "மகிழ்ச்சி":        "happy",
    "மகிழ்ச்சியாக":     "happy-ஆ",
    "மகிழ்ச்சியாய்":    "happy-ஆ",
    "வருத்தம்":         "sad",
    "வருத்தமாக":        "sad-ஆ",
    "கோபம்":            "கோபமா",
    "கோபமாக":          "கோபமா",
    "பயம்":             "பயமா",
    "பயமாக":            "பயமா",
    "உண்மையாக":         "நிஜமா",
    "உண்மையில்":        "நிஜமா",
    "நிச்சயமாக":        "definitely",
    "நிச்சயம்":         "definitely",
    "சந்தோஷம்":         "happy",
    "சந்தோஷமாக":        "happy-ஆ",
    "கவலை":             "tension",
    "கவலைப்படுகிறேன்":  "tension-ஆ இருக்கு",
    "கஷ்டம்":           "கஷ்டம்",       # keep — sounds natural
    "ஆச்சரியம்":        "surprised-ஆ",

    # ── VERBS — formal → spoken ───────────────────────────────
    "வருகிறேன்":        "வர்றேன்",
    "வருகிறாய்":        "வர்றே",
    "வருகிறான்":        "வர்றான்",
    "வருகிறாள்":        "வர்றா",
    "வருகிறார்":        "வர்றாரு",
    "வருகிறார்கள்":     "வர்றாங்க",
    "போகிறேன்":         "போறேன்",
    "போகிறாய்":         "போறே",
    "போகிறான்":         "போறான்",
    "போகிறாள்":         "போறா",
    "போகிறார்":         "போறாரு",
    "போகிறார்கள்":      "போறாங்க",
    "செய்கிறேன்":       "பண்றேன்",
    "செய்கிறாய்":       "பண்றே",
    "செய்கிறான்":       "பண்றான்",
    "செய்கிறாள்":       "பண்றா",
    "செய்கிறார்":       "பண்றாரு",
    "செய்கிறார்கள்":    "பண்றாங்க",
    "செய்கிறோம்":       "பண்றோம்",
    "பார்க்கிறேன்":     "பாக்கிறேன்",
    "பார்க்கிறான்":     "பாக்கிறான்",
    "பார்க்கிறாள்":     "பாக்கிறா",
    "பார்க்கிறார்":     "பாக்கிறாரு",
    "பார்க்கிறார்கள்":  "பாக்கிறாங்க",
    "பேசுகிறேன்":       "பேசுறேன்",
    "பேசுகிறான்":       "பேசுறான்",
    "பேசுகிறார்கள்":    "பேசுறாங்க",
    "தெரிகிறது":        "தெரியுது",
    "தெரிகிறதில்லை":    "தெரியல",
    "புரிகிறது":        "புரியுது",
    "புரிகிறதில்லை":    "புரியல",
    "இருக்கிறேன்":      "இருக்கேன்",
    "இருக்கிறான்":      "இருக்கான்",
    "இருக்கிறாள்":      "இருக்கா",
    "இருக்கிறார்கள்":   "இருக்காங்க",
    "கேட்கிறேன்":       "கேக்கிறேன்",
    "கேட்கிறான்":       "கேக்கிறான்",
    "சாப்பிடுகிறேன்":   "சாப்பிடுறேன்",
    "சாப்பிட்டேன்":     "சாப்பிட்டேன்",   # past tense ok
    "சென்றேன்":         "போனேன்",
    "வந்தார்":          "வந்தாரு",
    "சொன்னார்":         "சொன்னாரு",
    "போனார்":           "போனாரு",
    "நடக்கிறது":        "நடக்குது",
    "நடந்தது":          "நடந்துது",
    "ஆகிறது":           "ஆகுது",
    "வேண்டும்":         "வேணும்",
    "வேண்டாம்":         "வேணாம்",
    "கொண்டிருக்கிறேன்": "கிட்டிருக்கேன்",

    # ── ADVERBS / INTENSIFIERS ────────────────────────────────
    "மிகவும்":          "ரொம்ப",
    "மிகவும் நன்றாக":  "ரொம்ப நல்லா",
    "மிக":              "ரொம்ப",
    "அதிகமாக":          "ரொம்ப",
    "மெதுவாக":          "மெதுவா",
    "வேகமாக":           "வேகமா",
    "சரியாக":           "சரியா",
    "நன்றாக":           "நல்லா",
    "கொஞ்சம்":         "கொஞ்சம்",   # keep
    "இப்பொழுது":        "இப்போ",
    "இப்போது":          "இப்போ",
    "இப்போ":            "இப்போ",     # keep
    "எப்பொழுது":        "எப்போ",
    "அப்பொழுது":        "அப்போ",
    "திடீரென்று":       "திடீர்னு",
    "உடனே":             "உடனே",      # keep
    "நேரடியாக":         "directly",
    "முழுவதும்":        "fully",
    "ஏனென்றால்":        "because",
    "ஆனால்":            "ஆனா",
    "ஆனால்கூட":         "ஆனாலும்",
    "ஏனெனில்":          "because",
    "அதனால்":           "அதனால",
    "அதனால்தான்":       "அதனாலதான்",
    "இல்லையென்றால்":    "இல்லன்னா",
    "என்றால்":          "ன்னா",
    "என்னவென்றால்":     "என்னன்னா",
    "என்னவென்று":       "என்னன்னு",
    "என்று":            "ன்னு",
    "என்பது":           "ன்னு",

    # ── COMMON NOUNS ─────────────────────────────────────────
    "வீட்டில்":         "வீட்டுல",
    "வீட்டிற்கு":       "வீட்டுக்கு",
    "கல்லூரியில்":      "college-ல",
    "கல்லூரிக்கு":      "college-க்கு",
    "பள்ளியில்":        "school-ல",
    "நேரத்தில்":        "நேரத்துல",
    "நன்றி":            "thanks",
    "மன்னிக்கவும்":     "sorry",
    "சரியில்லை":        "சரியில்ல",
    "இல்லை":            "இல்ல",
    "தெரியாது":         "தெரியல",
    "புரியவில்லை":      "புரியல",
    "பரவாயில்லை":       "பரவாயில்ல",
}


def fix_formal_tamil(text: str) -> str:
    """Replace formal / cinematic Tamil with colloquial spoken forms.

    Also catches forbidden written-Tamil patterns that the LLM drifts into.
    Empty-string replacements (like எனவே → '') are cleaned up after.
    """
    for formal, colloquial in FORMAL_TO_COLLOQUIAL.items():
        text = text.replace(formal, colloquial)
    # Clean up any double-spaces left by empty replacements
    text = re.sub(r' {2,}', ' ', text).strip()
    return text

PHONETIC_SUBSTITUTIONS = {
    # The TTS reads written form rigidly — map to spoken form
    "அப்படியே":     "அப்டியே",
    "அப்படி":       "அப்டி",
    "இப்படியே":     "இப்டியே",
    "இப்படி":       "இப்டி",
    "எப்படி":       "எப்டி",
    "எப்படியே":     "எப்டியே",
    "கொண்டு":       "கிட்டு",
    "கொண்டிருக்":   "கிட்டிருக்",
    "விட்டு":       "விட்டு",       # keep
    "பண்ணிக்கொண்டு": "பண்ணிக்கிட்டு",
    "பார்த்துக்கொண்டு": "பாத்துக்கிட்டு",
    "போய்க்கொண்டே": "போய்க்கிட்டே",
    "என்னவென்று":   "என்னன்னு",
    "என்றால்":      "ன்னா",
    "அதனால்":       "அதனால",
    "ஆனால்":        "ஆனா",
    "வந்துவிட்டேன்": "வந்துட்டேன்",
    "போய்விட்டேன்": "போயிட்டேன்",
    "பார்த்துவிட்டேன்": "பாத்துட்டேன்",
    "சொல்லிவிட்டேன்": "சொல்லிட்டேன்",
    "பண்ணிவிட்டேன்": "பண்ணிட்டேன்",
    "ஆகிவிட்டது":   "ஆயிடுச்சு",
    "போய்விட்டது":  "போயிடுச்சு",
    "வந்துவிட்டது":  "வந்துடுச்சு",
    "பார்த்தேன்":   "பாத்தேன்",
    "பார்க்கவில்லை": "பாக்கல",
    "சொல்லவில்லை":  "சொல்லல",
    "வரவில்லை":     "வரல",
    "போகவில்லை":    "போகல",
    "தெரியவில்லை":  "தெரியல",
    "புரியவில்லை":  "புரியல",
    "கேட்கவில்லை":  "கேக்கல",
    "முடியவில்லை":  "முடியல",
    "இல்லாமல்":     "இல்லாம",
    "என்னோடு":      "என்கிட்ட",
    "உன்னோடு":      "உன்கிட்ட",
    "அவனோடு":       "அவன்கிட்ட",
    "அவளோடு":       "அவகிட்ட",
    "அவர்களோடு":    "அவங்ககிட்ட",
    "யாரோடு":       "யாருகிட்ட",
    "எனக்கு":       "எனக்கு",      # keep
    "உனக்கு":       "உனக்கு",      # keep
}

def phonetic_slurring(text: str) -> str:
    """
    Map structurally correct Tamil to spoken phonetic forms.
    This is what makes TTS sound like a real person vs a newsreader.
    Run AFTER fix_formal_tamil(), BEFORE transliterate_english().
    """
    for formal, spoken in PHONETIC_SUBSTITUTIONS.items():
        text = text.replace(formal, spoken)
    return text



# ── 5. EXPAND NUMBERS / SYMBOLS ───────────────────────────────────────────────

def expand_numbers(text: str) -> str:
    """Expand currency symbols and percentage signs for natural TTS reading.

    Sarvam bulbul:v3 reads '₹80' poorly — '80 rupees' is cleaner.
    Similarly '75%' → '75 percent' avoids mispronunciation.
    """
    text = re.sub(r'₹\s*(\d+)', r'\1 rupees', text)
    text = re.sub(r'(\d+)\s*%',  r'\1 percent', text)
    return text


# ── 6. EXPAND ABBREVIATIONS ───────────────────────────────────────────────────

# Only abbreviations that Sarvam reads poorly as-is.
# Common English loanwords (college, petrol, price, scene, etc.) are left
# untouched — Sarvam handles them correctly in natural Tanglish flow.
ENGLISH_TO_TAMIL = {
    r'\bHOD\b':  'Head of Department',
    r'\bCM\b':   'Chief Minister',
    r'\bDMK\b':  'D M K',
    r'\bTVK\b':  'T V K',
    r'\bBJP\b':  'B J P',
}


def transliterate_english(text: str) -> str:
    """Expand known abbreviations that Sarvam TTS reads poorly.

    Common English loanwords in natural Tanglish are intentionally left
    as-is — Sarvam bulbul:v3 handles them well in context.
    """
    for pattern, expanded in ENGLISH_TO_TAMIL.items():
        text = re.sub(pattern, expanded, text, flags=re.IGNORECASE)
    return text


# ── 7. PHONETIC OPTIMISATION ──────────────────────────────────────────────────

# Phrases that sound robotic in TTS → lighter phonetic alternatives.
# Principle: English insertions + shorter syllables = smoother flow.
PHONETIC_SUBSTITUTIONS = {
    "பணம் பணம்னு":      "money money-னு",
    "கதைக்களம்":         "story-யே",
    "மிகவும்":           "romba",
    "மிகவும் நல்ல":     "romba good",
    "கதை":               "story",          # only bare standalone
}

# Speakability reference scores (phrase → metrics dict).
# Higher = smoother TTS delivery. Used for reference / future scoring.
SPEAKABILITY_DB: dict[str, dict] = {
    "content-ஏ இல்லடா":      {"speakability": 9.5, "tts_smoothness": 9.1, "urbanity": 9.8},
    "story-யே இல்ல":          {"speakability": 9.3, "tts_smoothness": 9.0, "urbanity": 9.5},
    "romba over-ஆ போச்சு":   {"speakability": 8.8, "tts_smoothness": 8.5, "urbanity": 9.0},
    "waste of time":            {"speakability": 9.0, "tts_smoothness": 9.2, "urbanity": 8.5},
    "பணம் பணம்னு":            {"speakability": 5.5, "tts_smoothness": 4.8, "urbanity": 6.0},
    "கதைக்களம்":               {"speakability": 3.0, "tts_smoothness": 3.5, "urbanity": 2.0},
    "மிகவும்":                 {"speakability": 4.0, "tts_smoothness": 4.5, "urbanity": 3.0},
    "எனவே":                    {"speakability": 2.5, "tts_smoothness": 3.0, "urbanity": 1.5},
}


def speakability_score(phrase: str) -> dict:
    """Return speakability metrics for a phrase (lookup or estimate)."""
    if phrase in SPEAKABILITY_DB:
        return {"phrase": phrase, **SPEAKABILITY_DB[phrase]}
    # Heuristic: more English chars → smoother TTS flow
    english_ratio = len(re.findall(r'[a-zA-Z]', phrase)) / max(len(phrase), 1)
    score = round(5.0 + english_ratio * 4.0, 1)
    return {
        "phrase":          phrase,
        "speakability":    score,
        "tts_smoothness":  round(score - 0.3, 1),
        "urbanity":        round(score + english_ratio * 1.5, 1),
    }


def phonetic_optimize(text: str) -> str:
    """Replace heavy multi-syllable phrases with lighter TTS-friendly alternatives.

    Targets known bad-sounding patterns (pure Tamil compound words, written-Tamil
    forms) and replaces them with English-Tamil hybrid forms that flow more
    naturally in Tanglish TTS.

    Note: 'கதை' → 'story' is only applied if it appears as a standalone word
    to avoid corrupting compound words like 'கதைக்களம்' (handled separately).
    """
    for heavy, light in PHONETIC_SUBSTITUTIONS.items():
        if heavy == "கதை":
            text = re.sub(r'\bகதை\b', light, text)
        else:
            text = text.replace(heavy, light)
    return text


# ── 8. INTENSITY-BASED FRAGMENTATION ─────────────────────────────────────────

HIGH_INTENSITY = ["shocked", "outraged", "crying"]
MED_INTENSITY  = ["surprised", "laughing", "gossiping"]


def apply_intensity_fragmentation(text: str, emotion: str) -> str:
    """Pass-through: No longer mutating pauses."""
    return text


# ── 9. PROBABILISTIC SPEECH MUTATIONS ────────────────────────────────────────

def apply_speech_mutations(text: str, emotion: str) -> str:
    """Randomly apply human-like speech imperfections.

    Simulates: implied subjects, soft conversational fillers, and hard trail-offs.
    Applied probabilistically — at most 1 mutation fires per call.
    Strictly restricted from injecting English slang.
    """
    mutations_applied = 0

    # 15%: inject soft conversational filler at the start
    if mutations_applied < 1 and len(text) > 15:
        fillers = ["ம்ம்... ", "ஆன்... ", "அட... "]
        # Ensure we don't double up
        if not any(text.lstrip().startswith(f) for f in fillers):
            if random.random() < 0.15:
                text = random.choice(fillers) + text
                mutations_applied += 1

    # 15%: drop implied subject "நான்" at start
    if mutations_applied < 1 and re.match(r'^நான் \w', text):
        safe_to_drop = not re.match(r'^நான் .{1,15}[ஆ-ை]{1}[ப-வ]', text)
        if safe_to_drop and random.random() < 0.15:
            text = text[len("நான் "):]
            mutations_applied += 1

    # 15%: hard trail-off — cut after the last em-dash or mid-ellipsis.
    if mutations_applied < 1 and random.random() < 0.15:
        for sep in [" — ", "... "]:
            idx = text.rfind(sep)
            if idx > 20 and (len(text) - idx - len(sep)) > 8:
                text = text[:idx] + "..."
                mutations_applied += 1
                break

    return text


# ── 9b. TRUNCATION CLEANUP ────────────────────────────────────────────

# Short Tamil tokens that represent COMPLETE spoken words (safe to keep).
_SAFE_TAMIL_ENDINGS = (
    'டா', 'டே', 'ல்ல', 'மா', 'யா', 'னு', 'ங்க', 'க்கு',
    'ஆமா', 'போ', 'ஒண்ணு', 'வேண்', 'ngl', 'seriously',
)


def trim_incomplete_fragment(text: str) -> str:
    """Trim likely mid-word truncation fragments from the end of TTS text.

    Token limits can cut Tamil words mid-syllable. This detects short
    dangling purely-Tamil tokens (≤4 chars, no sentence-ending marker)
    and removes them, replacing with '...' to indicate trailing off.

    Conservative: only fires if the last token is short, pure Tamil script,
    and doesn't end with a known complete-word suffix.
    """
    # Already ends cleanly
    if text.endswith('...') or text.endswith('..........'):
        return text
    if re.search(r'[?!]$', text):
        return text

    # Check last whitespace-delimited token
    parts = text.rsplit(None, 1)
    if len(parts) != 2:
        return text

    last = parts[1]
    is_short     = len(last) <= 4
    is_pure_tamil = bool(re.match(r'^[஀-௿]+$', last))
    is_complete  = last.endswith(_SAFE_TAMIL_ENDINGS)

    if is_short and is_pure_tamil and not is_complete:
        trimmed = parts[0].rstrip(' ,')
        if not trimmed.endswith('...'):
            trimmed += '...'
        return trimmed

    return text


# ── 10. PAUSE INJECTION ───────────────────────────────────────────────────────

def inject_pauses(text: str) -> str:
    """Normalise ellipsis and em-dash markers for natural TTS pacing.

    Long runs (4+ dots) → '...'.
    Preserves natural soft pauses without stripping.
    Trailing commas removed to avoid an unnatural half-pause at the end.
    """
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'\.{2,3}', '...', text)
    text = re.sub(r'\s*—\s*', ' — ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r',\s*$', '', text)
    text = re.sub(r',\s*(\.+)', r' \1', text)
    return text.strip()


# ── 11. CLEAN FOR TTS (compat shim) ──────────────────────────────────────────

def clean_for_tts(text: str) -> str:
    """Backward-compat shim. Prefer preprocess() for the full pipeline."""
    text = remove_emotion_tags(text)
    text = fix_formal_tamil(text)
    text = expand_numbers(text)
    text = transliterate_english(text)
    text = phonetic_optimize(text)
    text = inject_pauses(text)
    return text.strip()


# ── 12. FULL PIPELINE ────────────────────────────────────────────────────────

def preprocess(text: str, profile: Optional[dict] = None, mutate: bool = True) -> dict:
    """Run the complete preprocessing pipeline on raw LLM text.

    Args:
        text:    Raw LLM output, may contain [emotion] tags.
        profile: Optional profile dict (from kavitha.json etc.).
        mutate:  If True, apply probabilistic speech mutations (default True).
                 Pass False for deterministic output (tests, evals).

    Returns:
        {
            "original":     original text,
            "emotion":      detected emotion string,
            "pace":         TTS pace value for this emotion,
            "tts_text":     final cleaned text ready for TTS,
            "display_text": clean text for terminal / subtitles,
        }

    Pipeline:
        Intent layer:  detect_emotion
        Clean layer:   remove_emotion_tags → fix_formal_tamil → expand_numbers
                       → transliterate_english → phonetic_optimize
        Shape layer:   convert_emotion_to_text → apply_intensity_fragmentation
                       → apply_speech_mutations (probabilistic)
        Render layer:  inject_pauses → NFC normalize → whitespace collapse
    """
    emotion = detect_emotion(text)

    # ── display path (no mutations / pause markers) ───────────────────────────
    display = remove_emotion_tags(text)
    display = fix_formal_tamil(display)
    display = phonetic_slurring(display)
    display = expand_numbers(display)
    display = transliterate_english(display)
    display = phonetic_optimize(display)

    # ── TTS path — full stack ─────────────────────────────────────────────────
    tts = remove_emotion_tags(text)
    tts = fix_formal_tamil(tts)
    tts = phonetic_slurring(tts)
    tts = expand_numbers(tts)
    tts = transliterate_english(tts)
    tts = phonetic_optimize(tts)
    tts = convert_emotion_to_text(tts, emotion)
    tts = apply_intensity_fragmentation(tts, emotion)
    tts = trim_incomplete_fragment(tts)
    if mutate:
        tts = apply_speech_mutations(tts, emotion)
    tts = inject_pauses(tts)
    tts = unicodedata.normalize('NFC', tts)
    tts = re.sub(r' {2,}', ' ', tts).strip()

    return {
        "original":     text,
        "emotion":      emotion,
        "pace":         EMOTION_PACE.get(emotion, 1.0),
        "tts_text":     tts,
        "display_text": display,
    }
