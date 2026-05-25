"""
core/persona_state.py
─────────────────────
Lightweight conversational state tracker for Kavitha.

Tracks emotional momentum across turns so the LLM receives context hints
that prevent jarring emotional disconnects between replies.

State is persisted to a JSON sidecar file (default: .kavitha_state.json)
so it survives across separate CLI invocations.

Usage:
    from core.persona_state import PersonaState
    state = PersonaState.load()
    hint  = state.emotional_context_hint()   # inject into system prompt
    # ... run LLM ...
    state.update(emotion="outraged", topic="petrol price")
    state.save()
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Emotion transition model ───────────────────────────────────────────────────
# What naturally follows each emotion in real conversation.

EMOTION_TRANSITIONS: dict[str, list[str]] = {
    "outraged":   [
        "continues the outrage with escalating heat",
        "decays into resigned exhaustion",
        "flips to sharp sarcasm",
    ],
    "shocked":    [
        "disbelief deepens — keeps repeating the same reaction",
        "shifts into outrage",
        "breaks into dark humour",
    ],
    "laughing":   [
        "stays playful and light",
        "pivots to sarcastically outraged",
        "trails off into boredom",
    ],
    "sighing":    [
        "stays in quiet resignation",
        "shifts to dark humour",
        "reluctant acceptance — moves on",
    ],
    "whispering": [
        "stays conspiratorial and hushed",
        "breaks into outrage at being found out",
        "trails off nervously",
    ],
    "gossiping":  [
        "whispers something even juicier",
        "pretends she shouldn't have said it",
        "trails off with implied meaning",
    ],
    "resigned":   [
        "stays in quiet resignation",
        "quiet frustration breaks through",
        "darkly accepts and moves on",
    ],
    "normal":     ["any emotional direction"],
}


# ── State dataclass ────────────────────────────────────────────────────────────

@dataclass
class PersonaState:
    """Per-session emotional continuity for Kavitha."""

    emotion_history: list[str] = field(default_factory=list)
    topic_history:   list[str] = field(default_factory=list)
    _state_file:     Path      = field(default=Path(".kavitha_state.json"),
                                       repr=False, compare=False)

    # ── Mutation ──────────────────────────────────────────────────────────────

    def update(self, emotion: str, topic: str) -> None:
        """Record a completed turn."""
        self.emotion_history.append(emotion)
        self.topic_history.append(topic)
        # Keep only the last 10 turns to avoid bloat
        self.emotion_history = self.emotion_history[-10:]
        self.topic_history   = self.topic_history[-10:]

    # ── Read-only properties ──────────────────────────────────────────────────

    @property
    def last_emotion(self) -> str:
        return self.emotion_history[-1] if self.emotion_history else "normal"

    @property
    def momentum(self) -> str:
        """Last 3 emotions as a readable chain, e.g. 'outraged → sighing'."""
        return " → ".join(self.emotion_history[-3:]) if self.emotion_history else ""

    def is_fresh(self) -> bool:
        """True if no turns have been recorded yet."""
        return len(self.emotion_history) == 0

    # ── LLM hint ─────────────────────────────────────────────────────────────

    def emotional_context_hint(self) -> str:
        """Return a natural-language hint for the LLM's next generation.

        Tells the LLM what emotional direction naturally follows the last
        turn so replies feel like a continuous conversation, not isolated
        random responses.
        """
        if self.is_fresh():
            return ""
        transitions = EMOTION_TRANSITIONS.get(self.last_emotion, ["any direction"])
        most_likely  = transitions[0]
        chain        = f" (chain: {self.momentum})" if len(self.emotion_history) > 1 else ""
        return (
            f"Previous emotion: {self.last_emotion}{chain}. "
            f"Natural continuation: {most_likely}."
        )

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist state to JSON sidecar file."""
        payload = {
            "emotion_history": self.emotion_history,
            "topic_history":   self.topic_history,
        }
        try:
            self._state_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass  # non-fatal — state is in-memory anyway

    @classmethod
    def load(cls, state_file: Optional[Path] = None) -> "PersonaState":
        """Load persisted state, or return a fresh state if none exists."""
        path = state_file or Path(".kavitha_state.json")
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                return cls(
                    emotion_history=raw.get("emotion_history", []),
                    topic_history=raw.get("topic_history", []),
                    _state_file=path,
                )
            except (json.JSONDecodeError, KeyError):
                pass
        return cls(_state_file=path)

    @classmethod
    def reset(cls, state_file: Optional[Path] = None) -> "PersonaState":
        """Wipe state and return a fresh instance."""
        path = state_file or Path(".kavitha_state.json")
        if path.exists():
            path.unlink()
        return cls(_state_file=path)
