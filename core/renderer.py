import re
from typing import Tuple

# ── 0. NORMALIZATION PATTERNS ─────────────────────────────────────────────────
# Fix common LLM spelling variations of Tanglish before rendering
NORMALIZATION_PATTERNS = [
    (r'\biruku\b', 'irukku'),
    (r'\bila\b', 'illa'),
    (r'\bpanrein\b', 'panren'),
    (r'\bpannuren\b', 'panren'),
]

# ── 1. PHRASE PATTERNS ────────────────────────────────────────────────────────
# Context-heavy multi-word patterns. Priority over single words.
PHRASE_PATTERNS = [
    (r'\bhot ah\b', 'hot-ஆ', 'ஹாட் ஆ'),
    (r'\bover ah\b', 'over-ஆ', 'ஓவரா'),
    (r'\bscene ah\b', 'scene-ஆ', 'சீனா'),
    (r'\bpadikkave illa\b', 'படிக்கவே இல்ல', 'படிக்கவே இல்ல'),
    (r'\bthaanga mudila\b', 'தாங்க முடியல', 'தாங்க முடியல'),
    (r'\bepdi irukku\b', 'எப்டி இருக்கு', 'எப்டி இருக்கு'),
    (r'\bper enna\b', 'பேரு என்ன', 'பேரு என்ன'),
    (r'\ben peru\b', 'என் பேரு', 'என் பேரு'),
    (r'\btension ah\b', 'tension-ஆ', 'டென்ஷன் ஆ'),
]

# ── 1.5. MORPHOLOGY PATTERNS ──────────────────────────────────────────────────
# Generalized grammar patterns (e.g., "-ae" emphasis, "pannalam").
MORPHOLOGY_PATTERNS = [
    # ── Emphasis & Focus
    (r'\b([a-zA-Z]+)-ae\b', r'\1-ஏ', r'\1 ஏ'),
    (r'\b([a-zA-Z]+)-a than\b', r'\1-ஆ தான்', r'\1 ஆ தான்'),
    
    # ── Questions
    (r'\b([a-zA-Z]+)-la\b', r'\1-ல', r'\1 ல'),
    (r'\b([a-zA-Z]+)-ma\b', r'\1-மா', r'\1 மா'),
    (r'\b([a-zA-Z]+)-a\b', r'\1-ஆ', r'\1 ஆ'),
    
    # ── Completion / State
    (r'\b([a-zA-Z]+)-achu\b', r'\1-ஆச்சு', r'\1 ஆச்சு'),
    (r'\b([a-zA-Z]+)-ruchu\b', r'\1-ருச்சு', r'\1 ருச்சு'),
    
    # ── Respect / Plural
    (r'\b([a-zA-Z]+)-nga\b', r'\1-ங்க', r'\1 ங்க'),
    
    # ── Compound Verbs
    (r'\b([a-zA-Z]+) pannalam\b', r'\1 பண்ணலாம்', r'\1 பண்ணலாம்'),
    (r'\b([a-zA-Z]+) pannitu\b', r'\1 பண்ணிட்டு', r'\1 பண்ணிட்டு'),
    (r'\b([a-zA-Z]+) vechitu\b', r'\1 வச்சிட்டு', r'\1 வச்சிட்டு'),
    (r'\b([a-zA-Z]+) panra\b', r'\1 பண்ற', r'\1 பண்ற'),
    (r'\b([a-zA-Z]+) panren\b', r'\1 பண்றேன்', r'\1 பண்றேன்'),
    (r'\b([a-zA-Z]+) pannala\b', r'\1 பண்ணல', r'\1 பண்ணல'),
    (r'\b([a-zA-Z]+) vandhuruchu\b', r'\1 வந்துருச்சு', r'\1 வந்துருச்சு'),
    (r'\b([a-zA-Z]+) poiruchu\b', r'\1 போயிருச்சு', r'\1 போயிருச்சு'),
    (r'\b([a-zA-Z]+) irukka\b', r'\1 இருக்கா', r'\1 இருக்கா'),
    (r'\b([a-zA-Z]+) illa\b', r'\1 இல்ல', r'\1 இல்ல'),
]

# ── 2. WORD PATTERNS ─────────────────────────────────────────────────────────
# Single word mappings for Tanglish to colloquial Tamil.
WORD_PATTERNS = {
    # Basic conversation
    "sema":      ("செம", "செமா"),
    "aan":       ("ஆன்", "ஆன்"),
    "mmm":       ("ம்ம்", "ம்ம்"),
    "irukku":    ("இருக்கு", "இருக்கு"),
    "la":        ("ல", "லா"),
    "da":        ("டா", "டா"),
    "di":        ("டி", "டி"),
    "saaptuten": ("சாப்ட்டேன்", "சாப்ட்டேன்"),
    "nalla":     ("நல்லா", "நல்லா"),
    "irukken":   ("இருக்கேன்", "இருக்கேன்"),
    "aprom":     ("அப்றம்", "அப்றம்"),
    "vera":      ("வேற", "வேற"),
    "enna":      ("என்ன", "என்ன"),
    "panra":     ("பண்ற", "பண்ற"),
    "panla":     ("பண்ணல", "பண்ணல"),
    "pannala":   ("பண்ணல", "பண்ணல"),
    "sollu":     ("சொல்லு", "சொல்லு"),
    "solluda":   ("சொல்லுடா", "சொல்லுடா"),
    "poda":      ("போடா", "போடா"),
    "illa":      ("இல்ல", "இல்ல"),
    "illada":    ("இல்லடா", "இல்லடா"),
    "kudichiten":("குடிச்சிட்டேன்", "குடிச்சிட்டேன்"),
    "pochu":     ("போச்சு", "போச்சு"),
    "matikitiya":("மாட்டிக்கிட்டியா", "மாட்டிக்கிட்டியா"),
    
    # Pronouns & Kinship
    "avanga":    ("அவங்க", "அவங்க"),
    "ivanga":    ("இவங்க", "இவங்க"),
    "avaru":     ("அவரு", "அவரு"),
    "ivaru":     ("இவரு", "இவரு"),
    "naanga":    ("நாங்க", "நாங்க"),
    "neenga":    ("நீங்க", "நீங்க"),
    "ungalukku": ("உங்களுக்கு", "உங்களுக்கு"),
    "ennoda":    ("என்னோட", "என்னோட"),
    "unnoda":    ("உன்னோட", "உன்னோட"),
    "enakku":    ("எனக்கு", "எனக்கு"),
    "unakku":    ("உனக்கு", "உனக்கு"),
    
    # Verbs
    "varren":    ("வர்றேன்", "வர்றேன்"),
    "poren":     ("போறேன்", "போறேன்"),
    "panren":    ("பண்றேன்", "பண்றேன்"),
    "paakuren":  ("பாக்கிறேன்", "பாக்கிறேன்"),
    "pesuren":   ("பேசுறேன்", "பேசுறேன்"),
    "theriyuthu":("தெரியுது", "தெரியுது"),
    "theriyala": ("தெரியல", "தெரியல"),
    "puriyuthu": ("புரியுது", "புரியுது"),
    "puriyala":  ("புரியல", "புரியல"),
    "irukkan":   ("இருக்கான்", "இருக்கான்"),
    "irukka":    ("இருக்கா", "இருக்கா"),
    "irukkanga": ("இருக்காங்க", "இருக்காங்க"),
    "kekkuren":  ("கேக்கிறேன்", "கேக்கிறேன்"),
    "kekkuran":  ("கேக்கிறான்", "கேக்கிறான்"),
    "ponen":     ("போனேன்", "போனேன்"),
    "vandharu":  ("வந்தாரு", "வந்தாரு"),
    "sonnaru":   ("சொன்னாரு", "சொன்னாரு"),
    "ponaru":    ("போனாரு", "போனாரு"),
    "nadakkuthu":("நடக்குது", "நடக்குது"),
    "venum":     ("வேணும்", "வேணும்"),
    "venam":     ("வேணாம்", "வேணாம்"),
    
    # Adverbs / States
    "romba":     ("ரொம்ப", "ரொம்ப"),
    "konjam":    ("கொஞ்சம்", "கொஞ்சம்"),
    "ippo":      ("இப்போ", "இப்போ"),
    "eppo":      ("எப்போ", "எப்போ"),
    "appo":      ("அப்போ", "அப்போ"),
    "udane":     ("உடனே", "உடனே"),
    "nijama":    ("நிஜமா", "நிஜமா"),
    
    # Nouns
    "veetla":    ("வீட்டுல", "வீட்டுல"),
    "college":   ("college", "கால்லேஜ்"),
    "school":    ("school", "ஸ்கூல்"),
    "amma":      ("அம்மா", "அம்மா"),
    "appa":      ("அப்பா", "அப்பா"),
    "thambi":    ("தம்பி", "தம்பி"),
    "akka":      ("அக்கா", "அக்கா"),
    "thangachi": ("தங்கச்சி", "தங்கச்சி"),
    "annan":     ("அண்ணன்", "அண்ணன்"),
    
    # Common Particles
    "aama":      ("ஆமா", "ஆமா"),
    "aamam":     ("ஆமாம்", "ஆமாம்"),
    "sari":      ("சரி", "சரி"),
    "seri":      ("சரி", "சரி"),
    "ok":        ("ok", "ஓகே"),
    "thanks":    ("thanks", "தேங்க்ஸ்"),
    "sorry":     ("sorry", "சாரி"),
    "paravayilla":("பரவாயில்ல", "பரவாயில்ல"),
    "innum":     ("இன்னும்", "இன்னும்"),
    "kandippa":  ("கண்டிப்பா", "கண்டிப்பா"),
}

# ── 3. POST PROCESSORS ───────────────────────────────────────────────────────
EMOTION_TAGS = [
    "shocked", "laughing", "outraged", "sighing",
    "whispering", "gossiping", "resigned", "surprised", "crying",
    "excited", "calm", "normal", "playful"
]

EMOTION_PACE = {
    "calm": 0.96,
    "normal": 0.98,
    "sighing": 0.90,
    "playful": 1.00,
    "outraged": 1.03,
}

def extract_emotion(text: str) -> Tuple[str, str]:
    """Extract [emotion] tag and return (emotion, clean_text)."""
    emotion = "normal"
    lower = text.lower()
    for tag in EMOTION_TAGS:
        if f"[{tag}]" in lower:
            emotion = tag
            break
    clean_text = re.sub(r'\[.*?\]', '', text).strip()
    return emotion, clean_text

def _apply_patterns(text: str, target: str) -> str:
    """Helper to apply phrase and word patterns for a target (display or tts)."""
    # 0. Apply Normalization
    for pattern, replacement in NORMALIZATION_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 1. Apply phrases
    for pattern, display_rep, tts_rep in PHRASE_PATTERNS:
        replacement = display_rep if target == "display" else tts_rep
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    # 1.5 Apply morphology patterns
    for pattern, display_rep, tts_rep in MORPHOLOGY_PATTERNS:
        replacement = display_rep if target == "display" else tts_rep
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    
    # 2. Apply words safely keeping punctuation
    def repl(match):
        word = match.group(0)
        clean_word = word.lower()
        if clean_word in WORD_PATTERNS:
            display_rep, tts_rep = WORD_PATTERNS[clean_word]
            return display_rep if target == "display" else tts_rep
        return word # Keep original Tanglish word

    # Match alphabet sequences
    text = re.sub(r'[a-zA-Z]+', repl, text)
    return text

def compile_spoken_tamil(tanglish_text: str) -> dict:
    """
    The Spoken Tamil Compiler.
    Takes pure conversational Tanglish from the LLM and dual-renders it.
    """
    emotion, clean_tanglish = extract_emotion(tanglish_text)
    
    display_text = _apply_patterns(clean_tanglish, target="display")
    tts_text = _apply_patterns(clean_tanglish, target="tts")
    
    # Cleanup extra spaces
    display_text = re.sub(r' {2,}', ' ', display_text).strip()
    tts_text = re.sub(r' {2,}', ' ', tts_text).strip()
    
    return {
        "original": tanglish_text,
        "emotion": emotion,
        "pace": EMOTION_PACE.get(emotion, 0.98),
        "tts_text": tts_text,
        "display_text": display_text
    }
