"""
All the knobs in one place.

Secrets do NOT live here and do NOT live in this folder. Copy .env.example to
~/.secrets/vtuber.env and put your key there. Anything that can read this
project - git, a zip you share, an AI assistant you point at the folder -
still cannot read that file. Override the location with VTUBER_ENV.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_SECRETS = Path(os.getenv("VTUBER_ENV", Path.home() / ".secrets" / "vtuber.env"))
load_dotenv(_SECRETS if _SECRETS.exists() else None)

# Fail loudly, and say where we looked. Without this a wrong path shows up
# much later as a confusing auth error from the API client - the same kind of
# silent hang that cost you an evening on the model name.
if not os.getenv("LLM_API_KEY"):
    raise SystemExit(
        f"No LLM_API_KEY found.\n"
        f"  Looked in: {_SECRETS}\n"
        f"  Exists:    {_SECRETS.exists()}\n"
        f"  Fix: copy .env.example there and put your key in it,\n"
        f"       or set VTUBER_ENV to wherever you keep it."
    )


@dataclass
class Config:
    # ---------- BRAIN ----------
    # Any OpenAI-compatible endpoint works here.
    #   Cloud:  https://api.openai.com/v1           (set LLM_API_KEY)
    #   Local:  http://localhost:11434/v1           (Ollama, key can be "ollama")
    #   Local:  http://localhost:1234/v1            (LM Studio)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "not-needed")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

    # Short replies = low latency = feels alive. This is the single most
    # important dial for "does it feel like a streamer or a chatbot".
    max_tokens: int = 120
    temperature: float = 0.9

    # ---------- VOICE ----------
    # edge-tts is free, needs no API key, and is fast. Swap later (see voice.py).
    tts_voice: str = os.getenv("TTS_VOICE", "en-US-AnaNeural")
    tts_rate: str = os.getenv("TTS_RATE", "+18%")  # a bit fast, like a streamer
    tts_pitch: str = os.getenv("TTS_PITCH", "+8Hz")

    # ---------- EARS ----------
    whisper_model: str = os.getenv("WHISPER_MODEL", "base.en")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")  # "cuda" if you have one
    sample_rate: int = 16000
    # Energy threshold for the toy VAD. Raise if it triggers on room noise.
    vad_threshold: float = float(os.getenv("VAD_THRESHOLD", "0.015"))
    vad_silence_sec: float = 0.8  # how long a pause ends your turn

    # ---------- PERSONA ----------
    char_name: str = os.getenv("CHAR_NAME", "Mika")
    persona_file: str = os.getenv("PERSONA_FILE", "persona.md")

    # ---------- MEMORY ----------
    history_turns: int = 12  # rolling window before we summarise

    # ---------- FACE ----------
    vts_url: str = os.getenv("VTS_URL", "ws://localhost:8001")
    vts_enabled: bool = os.getenv("VTS_ENABLED", "false").lower() == "true"

    stop_words: list[str] = field(default_factory=lambda: ["\nUser:", "\nChat:"])


cfg = Config()
