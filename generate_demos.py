import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()
from tts.sarvam import SarvamTTS

# Initialize TTS
tts = SarvamTTS(speaker="priya", model="bulbul:v3")

# Ensure output directory exists
out_dir = Path("frontend/public/audio")
out_dir.mkdir(parents=True, exist_ok=True)

# Define the demos
demos = [
    {
        "id": "raw-0",
        "text": "என்னுடைய தொலைபேசியில் மின்சாரம் இல்லை.",
        "pace": 1.0
    },
    {
        "id": "vox-0",
        "text": "ம்ம்... charge பண்ணி வச்சிருக்கேன்...",
        "pace": 0.98
    },
    {
        "id": "raw-1",
        "text": "நண்பரே, இது மிகவும் சலிப்பாக இருக்கிறது.",
        "pace": 1.0
    },
    {
        "id": "vox-1",
        "text": "அட டேய்... செம மொக்க தான்...",
        "pace": 1.0
    },
    {
        "id": "raw-2",
        "text": "நான் படிக்க அமர்ந்தவுடன் எனக்கு உறக்கம் வந்துவிட்டது.",
        "pace": 1.0
    },
    {
        "id": "vox-2",
        "text": "ஆன்... உடனே தூக்கம் வந்துருச்சு...",
        "pace": 0.96
    }
]

for d in demos:
    out_path = out_dir / f"{d['id']}.wav"
    print(f"Generating {d['id']} -> {out_path} ...")
    tts.save(d['text'], str(out_path), pace=d['pace'])

print("All audio files generated successfully!")
