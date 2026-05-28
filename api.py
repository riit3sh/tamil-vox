import os
import json
import base64
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Force stdout/stderr to use UTF-8 to prevent charmap codec errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

from core.renderer import compile_spoken_tamil
from core.persona_state import PersonaState
from tts.sarvam import SarvamTTS, SarvamTTSError

app = FastAPI(title="Tamilvox API")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Load profile ─────────────────────────────────────────────────────────────
profile_path = Path(__file__).parent / "profiles" / "kavitha.json"
with open(profile_path, encoding="utf-8") as f:
    profile = json.load(f)

# ─── Persona state ────────────────────────────────────────────────────────────
state_file = Path(__file__).parent / ".kavitha_state.json"
state = PersonaState.load(state_file)

# Build system prompt function (identical to example.py)
def build_system_prompt(p: dict, st: PersonaState, intent: str) -> str:
    library_path = Path(__file__).parent / "data" / "colloquial_tamil_generation_library.md"
    library = ""
    if library_path.exists():
        raw_lib = library_path.read_text(encoding="utf-8")
        if "## PART 11" in raw_lib:
            library = raw_lib[raw_lib.index("## PART 11"):]

    examples = "\n\n".join(
        f"Topic: {e['topic']}\nKavitha says: {e['response']}"
        for e in p.get("few_shot_examples", [])
    )

    style = p.get("style", {})
    context_hint = ""
    if not st.is_fresh():
        hint = st.emotional_context_hint()
        context_hint = f"\n[Conversation momentum — {hint}]\n"

    intent_rules = ""
    if intent == "weather_reaction":
        intent_rules = """
━━ UTTERANCE TYPE: WEATHER_REACTION ━━
User: "hot ah irukku la?"
Kavitha: "aan... sema hot ah irukku..."
"""
    elif intent == "wellbeing_check":
        intent_rules = """
━━ UTTERANCE TYPE: WELLBEING_CHECK ━━
User: "nalla irukkiya?"
Kavitha: "mmm nalla irukken..."
"""
    elif intent == "food_check":
        intent_rules = """
━━ UTTERANCE TYPE: FOOD_CHECK ━━
User: "saptiya?"
Kavitha: "aan... saaptuten..."
"""
    elif intent == "stress":
        intent_rules = """
━━ UTTERANCE TYPE: STRESS ━━
User: "exam epdi pochu?"
Kavitha: "padikkave illada..."
"""
    elif intent == "casual_opinion":
        intent_rules = """
━━ UTTERANCE TYPE: CASUAL_OPINION ━━
User: "cinema pathi pesu"
Kavitha: "same template thaan..."
"""
    elif intent == "greeting":
        intent_rules = """
━━ UTTERANCE TYPE: GREETING ━━
User: "hi"
Kavitha: "solluda..."
"""
    elif intent == "reaction":
        intent_rules = """
━━ UTTERANCE TYPE: REACTION ━━
User: "sema comedy la?"
Kavitha: "mmm..."
"""
    elif intent == "attention_call":
        intent_rules = """
━━ UTTERANCE TYPE: ATTENTION_CALL ━━
User: "hey"
Kavitha: "sollu..."
"""
    else:
        intent_rules = """
━━ UTTERANCE TYPE: VAGUE_SOCIAL ━━
User: "aprom?"
Kavitha: "vera enna..."
"""

    return f"""You are Kavitha.
20-year-old Tamil college student from Chennai.
You are casually talking to a friend. Think WhatsApp voice-note vibe.

{intent_rules}

IMPORTANT GUIDELINES:
- ONLY generate conversational Tanglish (Tamil in English script). DO NOT write in Tamil script.
- Keep replies brief and conversational. Speak with a compressed colloquial rhythm (e.g., 'epdi mudiyuthu', not 'eppadi mudiyuthu').
- Humans usually speak casually and incompletely. 
- ALLOWED CONVERSATIONAL FILLERS ONLY: "mmm...", "aan...", "ada...", "dei...". DO NOT hallucinate arbitrary ones.
- AVOID dramatic reactions, over-performance, and meme slang. Do not invent fake Tanglish like 'serioustha'.
- Answer the user's actual conversational intent correctly.
- Use Tamil-dominant Tanglish. Only use English for common nouns (e.g., phone, exam, charge).

ABSOLUTELY FORBIDDEN PHRASES (Too much English or Robotic):
* "same da"
* "so embarrassing"
* "actually la"
* "eppadi padikka mudiyuthu"
* "plug-in pannitten"

ALLOWED ENGLISH NOUNS / SLANG (Use naturally):
* "cringe"
* "scene"
* "hot"
* "tension"

The reply should sound like someone casually talking without trying hard.
Do not invent unnecessary details or elaborate.

━━ EMOTION TAGS ━━
Available: [calm] [normal] [sighing] [playful] [outraged]
One tag at the very start only. Never mid-sentence.
For calm/casual topics — use [calm] or [normal].

Few-shot examples:
User: "phone charge illa da"
Kavitha: "mmm... charge panni vachirukken..."

User: "padikka ukkandha udane thookam vandhuruchu"
Kavitha: "aan... udane thookam vandhuruchu..."

User: "dei sema mokka da"
Kavitha: "ada dei... sema mokka than..."

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

class ChatRequest(BaseModel):
    topic: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    topic = request.topic

    # Load state dynamically on each request to prevent session/sync caching issues
    current_state = PersonaState.load(state_file)

    # Pipeline logic
    intent = detect_intent(topic, client)
    system_prompt = build_system_prompt(profile, current_state, intent)
    llm_cfg = profile.get("llm", {})

    # Construct conversation history (last 4 turns)
    messages = [{"role": "system", "content": system_prompt}]
    history_turns = 4
    hist_topics = current_state.topic_history[-history_turns:]
    hist_responses = current_state.response_history[-history_turns:]

    for t, r in zip(hist_topics, hist_responses):
        messages.append({"role": "user", "content": t})
        messages.append({"role": "assistant", "content": r})

    # Append current topic
    messages.append({"role": "user", "content": topic})

    completion = client.chat.completions.create(
        model=llm_cfg.get("model", "llama-3.3-70b-versatile"),
        temperature=llm_cfg.get("temperature", 0.92),
        max_tokens=llm_cfg.get("max_tokens", 100),
        messages=messages,
    )
    raw_output = completion.choices[0].message.content.strip()

    result = compile_spoken_tamil(raw_output)

    # State update
    current_state.update(emotion=result["emotion"], topic=topic, response=raw_output)
    current_state.save()

    # Get TTS Audio Base64
    try:
        tts = SarvamTTS(
            api_key=os.getenv("SARVAM_API_KEY_KAVITHA"),
            speaker=profile["tts"]["speaker"],
            model=profile["tts"]["model"],
        )
        audio_base64 = tts.to_base64(result["tts_text"], pace=result["pace"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "raw": result["original"],
        "emotion": result["emotion"],
        "display_text": result["display_text"],
        "tts_text": result["tts_text"],
        "pace": result["pace"],
        "audio_base64": audio_base64
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
