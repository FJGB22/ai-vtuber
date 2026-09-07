# AI VTuber

A real-time AI streaming character in Python — it listens, thinks, and talks back
while it is still thinking. Built as a long-term study of low-latency, concurrent
AI systems rather than as a wrapper around a chat API.

The hard problem here is not "get an LLM to reply". It is getting the first word out
of the speakers fast enough that the character feels alive, while a microphone, a
speech recognizer, a token stream and an audio queue all run at the same time
without blocking each other.

```
  keyboard / chat ─┐
                   ├─> director ──> brain (LLM, streaming) ──> voice (TTS queue) ──> speakers
  microphone ──────┘       ^                   │
      (Whisper STT)        └──── interrupt ────┘             └──> face (VTube Studio)
```

## The latency trick

A naive implementation waits for the full LLM reply, sends it to TTS, then plays it:
two to four seconds of dead air per turn, and the illusion is gone.

`brain.py` streams tokens and emits **complete sentences** the moment each one closes.
`voice.py` holds a queue that starts speaking sentence one while the model is still
writing sentence two. First audio lands well under a second, and total latency stops
scaling with reply length.

Two consequences fall out of that design:

- `max_tokens` is capped at 120. Long replies feel like a chatbot, not a streamer —
  this is the single most sensitive dial in the project.
- Speech has to be interruptible. When the mic detects the user talking, the audio
  queue is flushed mid-sentence (`voice.interrupt()` in `main.py`).

## Modules

| File | Responsibility |
|---|---|
| `brain.py` | Async token streaming from an OpenAI-compatible endpoint, sentence chunking, rolling conversation window, `[emotion]` tag parsing |
| `voice.py` | Async TTS queue (edge-tts → ffplay), playback while generation continues, interrupt support |
| `ears.py` | Microphone capture, energy-gate VAD, `faster-whisper` transcription on CPU, in its own thread |
| `director.py` | Turn-taking. Arbitrates voice / chat / idle stimuli by priority so the character reacts to one thing at a time, and fills dead air after 25s |
| `face.py` | VTube Studio websocket API — expression hotkeys driven by the brain's emotion tag |
| `config.py` | Single dataclass of every knob; loads secrets from outside the repo and fails loudly if missing |
| `persona.md` | The character, as a prompt |
| `lab.py` | Measurement bench: `latency`, `tokens`, `jailbreak`, `drift` |

## Design decisions worth calling out

**Concurrency model is mixed on purpose.** The mic runs in an OS thread because
`sounddevice` blocks on a hardware buffer; everything else runs as asyncio tasks on
one event loop. The thread hands transcripts back to the loop rather than touching
async state directly.

**Secrets live outside the project directory.** `config.py` reads `~/.secrets/vtuber.env`
(override with `VTUBER_ENV`), not a `.env` inside the repo. A key that is never in the
folder cannot ride along in a commit, a zip, or a folder handed to a tool. Startup
aborts with the path it searched instead of surfacing later as a confusing 401.

**Chat input is fenced, not concatenated.** `wrap_chat()` strips newlines, truncates to
280 chars, and wraps viewer text in an explicit envelope. Live chat will attempt prompt
injection — this is mitigation, not a solution, and `lab.py jailbreak` exists to measure
how far it gets.

**The director is the underrated part.** A stream produces far more stimuli than the
character can answer. Without an arbiter you get a bot that replies to everything at
once, which reads as a demo rather than a personality.

## Running it

Requires Python 3.12 and ffmpeg on PATH.

```bash
cd starter
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# put your key in ~/.secrets/vtuber.env (template: .env.example)
python main.py                  # type to act as a chat viewer
python main.py --mic            # also listen to the microphone
```

Any OpenAI-compatible endpoint works as the brain — a cloud model, Ollama, or LM Studio.
The project targets a laptop with no discrete GPU: cloud brain, everything else local on
CPU. `starter/LAPTOP-SETUP.md` covers that tradeoff.

## Status

Phase 0 (foundations) is running end to end: text and voice in, streamed reply, spoken
output, optional Live2D expressions. Long-term memory, Twitch integration, moderation,
and autonomous behavior are later phases and deliberately not present — the roadmap in
`roadmap.html` tracks them.

## Stack

Python 3.12 · asyncio · OpenAI-compatible LLM API · edge-tts · faster-whisper · sounddevice · websockets
