"""
tts/sarvam.py
─────────────
Thin wrapper around the Sarvam AI TTS REST API (bulbul:v3).

Usage:
    from tts.sarvam import SarvamTTS
    tts = SarvamTTS(api_key="...", speaker="priya")
    tts.speak("என்னடா இது, விஜய் CM-ஆ?")          # play directly
    tts.save("text here", "out.wav")               # save to file
"""

import base64
import io
import os
import requests
import soundfile as sf
import sounddevice as sd
from typing import Optional


# Valid bulbul:v3 speakers (as of May 2026)
VALID_SPEAKERS = [
    "aditya", "ritu", "ashutosh", "priya", "neha", "rahul",
    "pooja", "rohan", "simran", "kavya", "amit", "dev",
    "ishita", "shreya", "ratan", "varun", "manan", "sumit",
    "roopa", "kabir", "aayan", "shubh", "advait", "anand",
    "tanya", "tarun",
]

TTS_URL = "https://api.sarvam.ai/text-to-speech"
DEFAULT_MODEL = "bulbul:v3"
DEFAULT_SPEAKER = "ritu"
DEFAULT_LANGUAGE = "ta-IN"


class SarvamTTSError(Exception):
    pass


class SarvamTTS:
    """Sarvam bulbul:v3 TTS client with optional direct playback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        speaker: str = DEFAULT_SPEAKER,
        model: str = DEFAULT_MODEL,
        language: str = DEFAULT_LANGUAGE,
        enable_preprocessing: bool = True,
    ):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        if not self.api_key:
            raise SarvamTTSError(
                "No Sarvam API key provided. "
                "Pass api_key= or set SARVAM_API_KEY in .env"
            )
        if speaker not in VALID_SPEAKERS:
            raise SarvamTTSError(
                f"Invalid speaker '{speaker}'. "
                f"Valid options: {', '.join(VALID_SPEAKERS)}"
            )
        self.speaker = speaker
        self.model = model
        self.language = language
        self.enable_preprocessing = enable_preprocessing

    def _call_api(self, text: str, pace: float = 1.0) -> bytes:
        """POST to Sarvam TTS API and return raw WAV bytes."""
        if not text.strip():
            raise SarvamTTSError("Text is empty after cleaning.")

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        body = {
            "inputs": [text],
            "target_language_code": self.language,
            "speaker": self.speaker,
            "model": self.model,
            "pace": pace,
            "enable_preprocessing": False,
        }

        print(f"  [DEBUG] SARVAM BODY: {body}")
        try:
            resp = requests.post(TTS_URL, headers=headers, json=body, timeout=30)
        except requests.RequestException as e:
            raise SarvamTTSError(f"Network error calling Sarvam TTS: {e}") from e

        if resp.status_code != 200:
            raise SarvamTTSError(
                f"Sarvam TTS returned {resp.status_code}: {resp.text[:300]}"
            )

        data = resp.json()
        audios = data.get("audios", [])
        if not audios:
            raise SarvamTTSError(f"No audio in Sarvam response: {data}")

        return base64.b64decode(audios[0])

    def to_bytes(self, text: str, pace: float = 1.0) -> bytes:
        """Return raw WAV bytes for the given text."""
        return self._call_api(text, pace=pace)

    def save(self, text: str, filepath: str, pace: float = 1.0) -> str:
        """Convert text to speech and save as WAV file. Returns filepath."""
        audio_bytes = self._call_api(text, pace=pace)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        return filepath

    def speak(self, text: str, pace: float = 1.0, emotion: str = "") -> None:
        """Convert text to speech and play immediately via sounddevice."""
        print(f"  [TTS] voice={self.speaker} pace={pace} emotion={emotion or 'normal'}")
        audio_bytes = self._call_api(text, pace=pace)
        buf = io.BytesIO(audio_bytes)
        data, samplerate = sf.read(buf)
        sd.play(data, samplerate)
        sd.wait()

    def speak_and_save(
        self, text: str, filepath: str, pace: float = 1.0, emotion: str = ""
    ) -> str:
        """Convert, save to file, AND play. Returns filepath."""
        print(f"  [TTS] voice={self.speaker} pace={pace} emotion={emotion or 'normal'}")
        audio_bytes = self._call_api(text, pace=pace)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        buf = io.BytesIO(audio_bytes)
        data, samplerate = sf.read(buf)
        sd.play(data, samplerate)
        sd.wait()
        return filepath
