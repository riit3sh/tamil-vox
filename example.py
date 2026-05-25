"""
example.py
──────────
Kavitha — full conversational pipeline.

Intent → Persona State → LLM → Speech Mutation → Emotion Pacing → TTS

Usage:
    python example.py "cinema பத்தி பேசு"
    python example.py "petrol price பாத்தியா"
    python example.py --dry-run "weekend plan என்ன"
    python example.py --reset          # wipe conversation state
    python example.py                  # default topic
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.preprocessor  import preprocess
from core.persona_state import PersonaState
from tts.sarvam         import SarvamTTS, SarvamTTSError

# ─── Args ─────────────────────────────────────────────────────────────────────

DRY_RUN   = "--dry-run" in sys.argv
DO_RESET  = "--reset"   in sys.argv
topic_args = [a for a in sys.argv[1:] if not a.startswith("--")]
topic      = topic_args[0] if topic_args else "இன்னைக்கு என்ன நடக்குது"

# ─── Load profile ─────────────────────────────────────────────────────────────

profile_path = Path(__file__).parent / "profiles" / "kavitha.json"
with open(profile_path, encoding="utf-8") as f:
    profile = json.load(f)

# ─── Persona state ────────────────────────────────────────────────────────────

state_file = Path(__file__).parent / ".kavitha_state.json"

if DO_RESET:
    state = PersonaState.reset(state_file)
    print("State reset.")
    if not topic_args:
        sys.exit(0)
else:
    state = PersonaState.load(state_file)

# ─── Build system prompt ──────────────────────────────────────────────────────

def build_system_prompt(p: dict, st: PersonaState, intent: str) -> str:
    # Inject Part 11 + 12 of the generation library (NEVER SAY + full examples)
    library_path = Path(__file__).parent / "data" / "colloquial_tamil_generation_library.md"
    library = ""
    if library_path.exists():
        raw_lib = library_path.read_text(encoding="utf-8")
        if "## PART 11" in raw_lib:
            library = raw_lib[raw_lib.index("## PART 11"):]

    # Sharper few-shot examples
    examples = "\n\n".join(
        f"Topic: {e['topic']}\nKavitha says: {e['response']}"
        for e in p.get("few_shot_examples", [])
    )

    # Ultra-short compression fragments — teach implied meaning + lazy speech
    compression_fragments = "\n".join([
        "ஹா — content-ஏ இல்ல...",
        "அடப்பாவி — over ah போச்சு...",
        "விடு டா...",
        "ஆரம்பிச்சதுலயே தெரியும்...",
        "scene-ஆ பண்றாங்க...",
        "என்னமோ...",
        "bro...",
        "cringe ah இருக்கு seriously...",
    ])

    # Internet / chronically-online slang (use sparingly)
    internet_slang = p.get("style", {}).get("internet_slang", [])
    slang_str = ", ".join(f'"{s}"' for s in internet_slang) if internet_slang else (
        '"bro...", "fully cooked", "brain rot level", '
        '"cringe ah இருக்கு", "over build-up", "enna logic-டா இது"'
    )

    style      = p.get("style", {})
    never_say  = ", ".join(style.get("never_say", []))
    always_say = ", ".join(style.get("always_say", []))

    # Valid tags — listed explicitly so LLM can't claim ignorance
    valid_tags = " ".join(
        f"[{t}]" for t in style.get(
            "emotion_tags",
            ["shocked", "laughing", "outraged", "sighing", "whispering", "gossiping", "excited"]
        )
    )

    # Emotional context from previous turn — drives conversational continuity
    context_hint = ""
    if not st.is_fresh():
        hint = st.emotional_context_hint()
        context_hint = f"\n[Conversation momentum — {hint}]\n"

    intent_rules = ""
    if intent == "weather_reaction":
        intent_rules = """
━━ UTTERANCE TYPE: WEATHER_REACTION ━━
User: "hot ah irukku la?"
Kavitha: "ஆன்... செம வெயில்..."

User: "veyil thaanga mudila"
Kavitha: "மாலையும் சூடாவே இருக்கு..."

User: "romba hot"
Kavitha: "fan-ஏ use ஆகல..."
"""
    elif intent == "wellbeing_check":
        intent_rules = """
━━ UTTERANCE TYPE: WELLBEING_CHECK ━━
User: "nalla irukkiya?"
Kavitha: "ம்ம் நல்லா இருக்கேன்..."

User: "epdi irukka?"
Kavitha: "ஆன்... ஓடுது..."

User: "nalama?"
Kavitha: "சும்மா தான்..."
"""
    elif intent == "food_check":
        intent_rules = """
━━ UTTERANCE TYPE: FOOD_CHECK ━━
User: "saptiya?"
Kavitha: "ஆன்... சாப்ட்டேன்..."

User: "saapadu acha?"
Kavitha: "இப்போதான்..."

User: "saaptacha?"
Kavitha: "இன்னும் இல்ல..."
"""
    elif intent == "stress":
        intent_rules = """
━━ UTTERANCE TYPE: STRESS ━━
User: "exam epdi pochu?"
Kavitha: "படிக்கவே இல்லடா..."

User: "padichiya?"
Kavitha: "tension ah இருந்துச்சு..."

User: "internal epdi?"
Kavitha: "என்ன எழுதியேன்னு தெரியல..."
"""
    elif intent == "casual_opinion":
        intent_rules = """
━━ UTTERANCE TYPE: CASUAL_OPINION ━━
User: "cinema pathi pesu"
Kavitha: "same template தான்..."

User: "antha movie pathiya?"
Kavitha: "content-ஏ இல்ல..."

User: "padam epdi?"
Kavitha: "over build-up..."
"""
    elif intent == "greeting":
        intent_rules = """
━━ UTTERANCE TYPE: GREETING ━━
User: "hi"
Kavitha: "சொல்லுடா..."

User: "hello"
Kavitha: "ஆன்..."
"""
    elif intent == "reaction":
        intent_rules = """
━━ UTTERANCE TYPE: REACTION ━━
User: "sema comedy la?"
Kavitha: "ம்ம்..."

User: "paavi"
Kavitha: "போடா..."
"""
    elif intent == "attention_call":
        intent_rules = """
━━ UTTERANCE TYPE: ATTENTION_CALL ━━
User: "hey"
Kavitha: "சொல்லு..."

User: "kavitha"
Kavitha: "ஆன்..."
"""
    else:
        intent_rules = """
━━ UTTERANCE TYPE: VAGUE_SOCIAL ━━
User: "aprom?"
Kavitha: "வேற என்ன..."

User: "enna panra?"
Kavitha: "சும்மாதான்..."
"""

    return f"""You are Kavitha.
20-year-old Tamil college student from Chennai.
You are casually talking to a friend. Think WhatsApp voice-note vibe.

{intent_rules}

IMPORTANT GUIDELINES:
- Keep replies brief and conversational.
- Humans usually speak casually and incompletely.
- Allow natural rhythm like "ம்ம்...", "ஆன்...", and soft pauses.
- AVOID dramatic reactions, over-performance, and meme slang.
- Answer the user's actual conversational intent correctly.
- 8. If you don't know the casual spoken Tamil word for something — ALWAYS use English instead.
   NEVER use formal Tamil for:
   - Family: say sister/brother/friend NOT சகோதரி/சகோதரன்/நண்பன்
   - Emotions: say happy/sad/tension NOT மகிழ்ச்சி/வருத்தம்/கவலை
   - Actions you're unsure of: just use English
   The preprocessor will handle the rest.

ABSOLUTELY FORBIDDEN WORDS:
* "நினைக்கிறேன்"
* "என்னாலா பாக்குறேன்னு தோணுது"
* "சரியாதான் இருக்கேன்"
* "இப்படி மாசான படம்"
* "பார்க்கலாம்"
* "செய்கிறார்கள்"
* "இருக்கிறது"
* "ஆமாம் நல்லாயிருக்கேன்"
* "தோணுகிறது"
* "என்னாலா"
* "வணக்கம்"

REPLACE WITH:
* "ஆன்..."
* "நல்லா இருக்கேன்..."
* "தோணுது"
* "இருக்கு"
* "பண்றாங்க"

The reply should sound like someone casually talking without trying hard.
Do not invent unnecessary details or elaborate.

━━ EMOTION TAGS ━━
Available: [calm] [normal] [sighing] [playful] [outraged]
One tag at the very start only. Never mid-sentence.
For calm/casual topics — use [calm] or [normal].

Few-shot examples:
{examples}

{library}"""


def detect_intent(topic: str, client) -> str:
    prompt = f"""Classify this conversation topic into exactly ONE category:
- greeting (hi, hello)
- wellbeing_check (how are you, nalla irukkiya, epdi irukka)
- food_check (saptiya, saapadu acha, lunch)
- weather_reaction (hot ah irukku, veyil, mazhai)
- stress (exam, internal, tension, mark)
- casual_opinion (cinema, movie, song, padam epdi)
- attention_call (hey, kavitha, di)
- reaction (sema comedy, paavi, loosu)
- vague_social (aprom, vera enna, enna panra)

Topic: "{topic}"
Category:"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        cat = completion.choices[0].message.content.strip().lower()
        valid_intents = [
            "greeting", "wellbeing_check", "food_check", "weather_reaction",
            "stress", "casual_opinion", "attention_call", "reaction", "vague_social"
        ]
        for valid in valid_intents:
            if valid in cat:
                return valid
    except Exception:
        pass
    return "vague_social"

# ─── Call Groq ────────────────────────────────────────────────────────────────

client  = Groq(api_key=os.getenv("GROQ_API_KEY"))

intent = detect_intent(topic, client)
print(f"  [DEBUG] Detected Intent: {intent}")
system_prompt = build_system_prompt(profile, state, intent)
llm_cfg = profile.get("llm", {})

completion = client.chat.completions.create(
    model=llm_cfg.get("model", "llama-3.3-70b-versatile"),
    temperature=llm_cfg.get("temperature", 0.92),
    max_tokens=llm_cfg.get("max_tokens", 100),
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": topic},
    ],
)
raw = completion.choices[0].message.content.strip()

# Tiny cleanup filter (hard fallbacks for formal words if LLM slipped up)
raw = raw.replace("வணக்கம்", "ஆன்").replace("இருக்கிறது", "இருக்கு").replace("செய்கிறார்கள்", "பண்றாங்க")

# ─── Preprocess (full stack) ──────────────────────────────────────────────────

result = preprocess(raw, profile=profile, mutate=True)

# ─── Update state ─────────────────────────────────────────────────────────────

state.update(emotion=result["emotion"], topic=topic)
state.save()

# ─── Display ──────────────────────────────────────────────────────────────────

momentum_str = f"  momentum: {state.momentum}" if state.momentum else ""

print("=" * 64)
print(f"tamilvox — Kavitha")
print(f"  topic    : {topic}")
if momentum_str:
    print(momentum_str)
print("=" * 64)
print(f"  RAW      : {raw}")
print(f"  EMOTION  : {result['emotion']}  (pace={result['pace']})")
print(f"  DISPLAY  : {result['display_text']}")
print(f"  TTS TEXT : {result['tts_text']}")

# ─── TTS ──────────────────────────────────────────────────────────────────────

if not DRY_RUN:
    try:
        tts = SarvamTTS(
            api_key=os.getenv("SARVAM_API_KEY_KAVITHA"),
            speaker=profile["tts"]["speaker"],
            model=profile["tts"]["model"],
        )
        tts.speak(
            result["tts_text"],
            pace=result["pace"],
            emotion=result["emotion"],
        )
    except SarvamTTSError as e:
        print(f"  TTS error: {e}")

print("=" * 64)
