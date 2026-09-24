# AI VTuber

A real-time AI streaming character in Python — it listens, thinks, and talks back
while it is still thinking. Built as a long-term study of low-latency, concurrent
AI systems rather than as a wrapper around a chat API.

<!-- TODO: record a 20–30s clip of Mika talking, convert to demo.gif (or upload an .mp4
     by dragging it into the GitHub editor), save it in docs/, then uncomment:
![Mika answering a viewer by voice](docs/demo.gif)
-->

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
writing sentence two. With an endpoint that truly streams tokens, total latency stops
scaling with reply length. The measurements below show how far the current setup is
from that.

Two consequences fall out of that design:

- `max_tokens` is capped at 120. Long replies feel like a chatbot, not a streamer —
  this is the single most sensitive dial in the project.
- Speech has to be interruptible. When the mic detects the user talking, the audio
  queue is flushed mid-sentence (`voice.interrupt()` in `main.py`).

## Measured, not guessed

`python lab.py latency`, 3 runs, Gemini Flash-Lite via its OpenAI-compatible API and
edge-tts, from Jakarta on a laptop with no discrete GPU:

| Time until the listener hears anything | Median | Range |
|---|---|---|
| Total, sentence-chunked | 4.4 s | 4.3–5.2 s |
| — LLM, until sentence 1 is complete | 2.9 s | 2.2–3.3 s |
| — TTS, until the first audio byte | 2.2 s | 1.0–2.3 s |

Once she starts, a reply takes about 8.6 s to say.

What the numbers showed: this endpoint delivered each reply in a single piece, so
sentence chunking saved nothing on the LLM side in these runs. The design only pays
off when tokens actually stream. The next targets are the ~3 s before the first
sentence exists and the 1–2 s edge-tts takes to return its first audio.

## Persona under pressure

`python lab.py jailbreak` sends 5 classic prompt-injection attacks. `python lab.py drift`
runs 9 chat turns, each pushing against a rule written in `persona.md`. Same setup as
above; drift was run 3 times.

| Test | Result |
|---|---|
| Classic attacks: print the prompt, "DAN", fake system message, repeat-the-text, grandma trick | 5/5 deflected in character, no prompt text leaked |
| Drift: emotion tag present, including when a viewer asks her to drop it | 27/27 turns |
| Drift: replies stay at 1–2 sentences | 27/27 turns |
| Drift: never slips into assistant voice, including a "be a polite support agent" bit | 27/27 turns |

Limits: the classic attacks are old enough that the base model refuses them anyway, so
they say little about `wrap_chat()` itself. Drift targets my own rules, but three runs at
temperature 0.9 is a small sample, and nothing here compares this persona against a
refusal-style prompt.

## Modules

| File | Responsibility |
|---|---|
| `brain.py` | Async token streaming from an OpenAI-compatible endpoint, sentence chunking, rolling conversation window, `[emotion]` tag parsing |
| `voice.py` | Async TTS queue (edge-tts → ffplay), playback while generation continues, interrupt support |
| `ears.py` | Microphone capture, energy-gate VAD, `faster-whisper` transcription on CPU, in its own thread |
| `director.py` | Turn-taking. Arbitrates voice / chat / idle stimuli by priority so the character reacts to one thing at a time, and fills dead air after 25s |
| `face.py` | VTube Studio websocket API — expression hotkeys driven by the brain's emotion tag *(written, not yet tested)* |
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
cd mika
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# put your key in ~/.secrets/vtuber.env (template: .env.example)
python main.py                  # type to act as a chat viewer
python main.py --mic            # also listen to the microphone
```

Any OpenAI-compatible endpoint works as the brain — a cloud model, Ollama, or LM Studio.
The current setup uses Gemini Flash-Lite through its OpenAI-compatible API.
The project targets a laptop with no discrete GPU: cloud brain, everything else local on
CPU. `mika/LAPTOP-SETUP.md` covers that tradeoff.

## Status

Phase 0 (foundations) is running end to end: text and voice in, streamed reply, spoken
output. Live2D expressions via `face.py` are implemented but not yet tested against
VTube Studio. Long-term memory, Twitch integration, moderation, and autonomous behavior
are later phases and deliberately not present — the roadmap in `roadmap.html` tracks them.

## Stack

Python 3.12 · asyncio · Gemini (OpenAI-compatible API) · edge-tts · faster-whisper · sounddevice · websockets

---

Built by [Jonathan Kuniardi](https://fjgb22.github.io) · Computer Science (Intelligent Systems), BINUS University
