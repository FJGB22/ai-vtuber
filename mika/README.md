# AI VTuber Starter

A ~400-line skeleton of the same architecture Neuro-sama uses. It is deliberately
small enough to read in one sitting and understand completely.

```
  keyboard/chat ─┐
                 ├─> director ──> brain (LLM, streaming) ──> voice (TTS) ──> speakers
  microphone ────┘        ^                    │
     (STT)                └── interrupt ───────┘             └──> face (VTube Studio)
```

| File | What it teaches |
|---|---|
| `brain.py` | Token streaming + sentence chunking. The latency trick. |
| `voice.py` | An audio queue that plays while the LLM is still writing. |
| `ears.py` | Mic capture, voice-activity detection, Whisper transcription. |
| `director.py` | Turn-taking. What she reacts to and when. The underrated part. |
| `face.py` | VTube Studio websocket API, expression control. |
| `persona.md` | Character as a prompt. Rewrite this a hundred times. |

> **No discrete GPU?** Read [`LAPTOP-SETUP.md`](LAPTOP-SETUP.md) first. Everything here
> works fine on a thin-and-light — you just put the LLM in the cloud instead of on your CPU.

## Run it

**1. Install ffmpeg** (for audio playback) — https://ffmpeg.org/download.html

**2. Install Python deps**

```bash
cd mika
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Pick a brain**

Local and free (needs a decent GPU to feel snappy):
```bash
# install from https://ollama.com then:
ollama pull llama3.1:8b
ollama serve
```

Or cloud (works on any laptop, costs cents per hour):
edit `.env` and point `LLM_BASE_URL` at an OpenAI-compatible endpoint.

**4. Configure and go**

```bash
cp .env.example .env     # edit it
python main.py           # type to act as chat
python main.py --mic     # also talk to her
```

## Your first four experiments

1. Set `max_tokens` to 500 in `config.py`. Notice how she instantly stops
   feeling like a streamer. Put it back. This is the most important lesson here.
2. Delete the sentence-chunking in `brain.py` and buffer the whole reply before
   speaking. Time the difference. That gap is what you spend the project fighting.
3. Rewrite `persona.md` to be someone else entirely. Personality is 90% prompt.
4. Try to jailbreak her through the chat input. You will succeed. That is
   Phase 5's problem, and every AI VTuber has it.

## What is deliberately missing

Long-term memory, Twitch, OBS, moderation, game playing, interruption handling
that actually works well. Those are the roadmap phases — build them yourself
rather than downloading them, that is the whole point of the project.
