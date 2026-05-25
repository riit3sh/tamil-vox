# tamilvox

Colloquial Tamil text preprocessor + Sarvam TTS wrapper.

Turns raw LLM output (with `[emotion]` tags, formal Tamil, English words)
into natural, spoken-Tamil audio via Sarvam bulbul:v3.

---

## What it does

```
Raw LLM text
    → detect emotion tag
    → remove [emotion] tags
    → inject natural onset / tail ("என்னடா இது —", "...என்னமோ போ")
    → fix formal Tamil → colloquial  (அவர்கள் → அவங்க)
    → transliterate English loanwords → Tamil script  (government → கவர்மென்ட்)
    → inject TTS pause markers  (... → , )
    → Sarvam bulbul:v3 TTS → audio
```

---

## Structure

```
tamilvox/
├── core/
│   └── preprocessor.py     ← all text transformation logic
├── tts/
│   └── sarvam.py           ← Sarvam TTS wrapper (speak / save / speak_and_save)
├── profiles/
│   └── kavitha.json        ← persona config (TTS speaker, LLM settings, style)
├── data/
│   └── colloquial_tamil_generation_library.md   ← reference word maps + rules
├── example.py              ← runnable demo
└── requirements.txt
```

---

## Quickstart

```bash
pip install -r requirements.txt
```

Set your Sarvam API key in `.env` (or in the parent project's `.env`):
```
SARVAM_API_KEY_KAVITHA=your_key_here
```

**Text-only dry run (no API key needed):**
```bash
python example.py --dry-run
```

**Full run with audio playback:**
```bash
python example.py
```

---

## Use in code

```python
from core.preprocessor import preprocess
from tts.sarvam import SarvamTTS

# Preprocess raw LLM output
result = preprocess("[outraged] அடப்பாவி, petrol price இன்னைக்கும் raise பண்ணிட்டாங்க!!")
print(result["emotion"])      # "outraged"
print(result["display_text"]) # clean text for subtitles/terminal
print(result["tts_text"])     # TTS-ready text with onset + pause markers

# Speak it
tts = SarvamTTS(api_key="...", speaker="priya")
tts.speak(result["tts_text"])
```

---

## Valid Sarvam bulbul:v3 speakers

Female: `priya`, `neha`, `pooja`, `simran`, `kavya`, `ishita`, `shreya`, `roopa`, `tanya`, `ritu`

Male: `aditya`, `ashutosh`, `rahul`, `rohan`, `amit`, `dev`, `ratan`, `varun`, `manan`, `sumit`, `kabir`, `aayan`, `shubh`, `advait`, `anand`, `tarun`

Set your preferred speaker in `profiles/kavitha.json` → `tts.speaker`.

---

## Adding a new persona

1. Copy `profiles/kavitha.json` → `profiles/yourname.json`
2. Edit `tts.speaker`, `style`, `few_shot_examples`
3. Pass the loaded profile to `preprocess(text, profile=profile)`
