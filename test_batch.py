import os
import time
from groq import Groq
from core.renderer import compile_spoken_tamil
from example import detect_intent, build_system_prompt
import json
from dotenv import load_dotenv
load_dotenv()

# Minimal mock of profile/state
profile = {
    "name": "Kavitha",
    "llm": {"model": "llama-3.3-70b-versatile", "temperature": 0.92, "max_tokens": 100}
}
class MockState:
    momentum = "calm \u2192 calm \u2192 calm"
    def is_fresh(self): return False
    def emotional_context_hint(self): return "Normal conversation."

state = MockState()

test_inputs = [
    "phone charge illa da",
    "padikka ukkandha udane thookam vandhuruchu",
    "dei sema mokka da",
    "innaiku fulla suthitu irunthe",
    "oru nalla paatu sollu",
    "exam result varudhu bayama irukku",
    "saptiya enna panra",
    "veyil mandaiya polakuthu",
    "movie paaka polama",
    "bore adikutha",
    "enna di aachu",
    "thookkam varla",
    "seri namba aprom peslam",
    "oru maadhiri irukku",
    "office la orey velai",
    "bus kedaikala nadanthu vandhen",
    "avanga enna sonnanga",
    "idhu thevaiya namakku",
    "amma thittitanga",
    "kaasu illa",
    "innum saapdala pasikuthu",
    "net sariya kedaikala",
    "yaarathu",
    "thala vali",
    "nalaiki leave ah",
    "avangala koopdu",
    "naan varala",
    "avasiyam ah",
    "eppadi irukka",
    "time aachu naan poren"
]

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

results = []
for topic in test_inputs:
    print(f"\n--- Testing: {topic} ---")
    intent = detect_intent(topic, client)
    prompt = build_system_prompt(profile, state, intent)
    
    try:
        completion = client.chat.completions.create(
            model=profile["llm"]["model"],
            temperature=profile["llm"]["temperature"],
            max_tokens=profile["llm"]["max_tokens"],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic},
            ],
        )
        tanglish_raw = completion.choices[0].message.content.strip()
        compiled = compile_spoken_tamil(tanglish_raw)
        
        print(f"RAW: {tanglish_raw}")
        print(f"DISPLAY: {compiled['display_text']}")
        print(f"TTS: {compiled['tts_text']}")
        
        results.append({
            "input": topic,
            "raw": tanglish_raw,
            "display": compiled['display_text'],
            "tts": compiled['tts_text']
        })
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)

with open("test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nDone testing.")
