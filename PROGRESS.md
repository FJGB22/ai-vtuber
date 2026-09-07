# Project log

This file is the memory that survives between chats. Update it at the end of every
session. When you start a new chat, paste this file in as the first message and you
skip all the re-explaining.

---

## Context to paste into a new chat

> I'm building an AI VTuber (Neuro-sama style) as a long-term learning project.
> Hardware: Lenovo IdeaPad Slim 5, Windows. AMD Ryzen 7 8845HS (8c/16t), Radeon 780M
> integrated graphics, 16 GB RAM, no discrete GPU. Python 3.12 (3.14 also installed).
> Stack: cloud LLM (OpenAI-compatible endpoint), edge-tts, faster-whisper base.en on CPU,
> VTube Studio planned for later.
> Project lives in C:\Users\Lenovo\ai-vtuber.
> I'm on **Phase N: <name>**. Here's my current code and progress log.

---

## Status

- **Current phase:** 0 — Foundations. Experiments done, moving to Phase 1.
- **Last worked on:** 2026-08-21
- **Machine:** IdeaPad Slim 5 · Ryzen 7 8845HS · Radeon 780M · 16 GB RAM · ~284 GB free
- **Environment:** Python 3.12 venv at `starter/.venv`. Activate with
  `.\.venv\Scripts\activate` from the `starter` folder — a new terminal is never
  activated, and `ModuleNotFoundError` almost always means you forgot.
- **Secrets:** the key lives at `C:\Users\Lenovo\.secrets\vtuber.env`, NOT in the
  project. `config.py` reads it from there (override with `VTUBER_ENV`) and exits
  loudly if it can't find it.
- **Working:** `python main.py` — she replies in text and speaks via edge-tts.
  `python lab.py <latency|tokens|jailbreak|drift>` — the measurement bench.
- **Next:** the Phase 0 learning track — see the section below. Not Phase 1 yet.

## Done

- [x] Phase 0 — Foundations
- [ ] Phase 1 — A character that types
- [ ] Phase 2 — Give it a voice
- [ ] Phase 3 — Give it ears
- [ ] Phase 4 — Give it a face
- [ ] Phase 5 — Put it on stream
- [ ] Phase 6 — Memory and a self
- [ ] Phase 7 — Agency
- [ ] Phase 8 — Operations

## Next session — the Phase 0 learning track

**Read this part first if you are a new chat.** The experiments in Phase 0 are done
and the prototype runs, but the Phase 0 *curriculum* has not been touched. On
2026-08-21 the assistant wrote almost all of the code and I ran commands and pasted
output. I ended the day understanding the system's behaviour and none of its
mechanics. That is the gap to close before Phase 1.

**Goal:** read every line of `starter/` without guessing what it does.

**The exam:** explain why the microphone runs in a thread but the TTS queue runs as
an asyncio task. The answer is spread across `ears.py`, `voice.py` and `main.py`.
When I can answer that unprompted, Phase 0 is genuinely finished.

**The trap:** skipping asyncio. Every component here is concurrent. Without the event
loop model I will spend months on deadlocks I cannot describe.

**How to teach me (I asked for this explicitly):**

- Concepts BEFORE code. Assume I am starting from zero and say so plainly.
- But keep each explanation short, then give me five to ten lines to type myself
  before moving on. No hour-long lecture followed by coding. A concept my hands never
  touched evaporates in a day — that is exactly what went wrong on 2026-08-21.
- **The assistant does not write the code.** Spec and failing tests from them, typing
  from me. If I ask them to just write it, they should refuse; that is the deal.
  Hints when I am stuck, not answers.
- Use MY files as the examples. Abstract asyncio tutorials are why people quit.
  I already run this code and want to understand it, which is the best possible
  motivation to learn from.
- Move fast until I hesitate, then slow down there. I will say "too fast" or
  "already know this".

**Order:**

1. Blocking vs non-blocking, and why it is a problem for a program that must listen
   and speak at the same time. This first — it gives everything else a reason to exist.
2. Type hints, dataclasses (`config.py` and `director.py` are full of both).
3. Generators (`brain.py`'s `async for sentence in brain.respond(...)`).
4. Context managers.
5. The heavy part: event loop, coroutines, tasks, `gather`, `Queue`,
   `run_in_executor`, threads, and the bridge between a thread and the loop.
6. Lighter, later: websockets and JSON-ish protocols (`face.py`), digital audio —
   sample rate, PCM, float32, RMS, buffers (`ears.py`).
7. Ongoing: venv, pip, git, reading someone else's repo without panicking.

**First exercises, once the concepts are in place** — three toy programs, none of
them about VTubers:

- a generator that yields complete sentences from a stream of characters
- an asyncio producer/consumer queue where the consumer runs while the producer is
  still producing
- a thread that pushes data into a running event loop

Those three ARE `brain.py`, `voice.py` and `ears.py` with the costume off.

## Measured on this machine

Numbers from `lab.py`, not from anyone's blog. Re-measure after any change that
touches the pipeline — that is the whole point of keeping the bench around.

| Thing | Value | Why it matters |
|---|---|---|
| LLM, first token | 0.8–1.5s | Only 14% of a conversational turn. |
| edge-tts, first audio byte | 0.7–1.4s | Scales with how much text you hand it. |
| **Speech rate** | **~15 chars/sec** | `chars / 15` = seconds she holds the floor. |
| One full turn | ~10.5s | 1.5s think + 0.7s synth + **8.3s talking**. |
| Sentence chunking gain | −0.04s | See below. It buys nothing *yet*. |

**The voice is the bottleneck, not the brain.** Everyone optimises the LLM. The LLM
is the smallest slice. What costs you a conversation is the 8 seconds where she is
talking and nobody can interrupt. This reframes Phase 3: `voice.interrupt()` is not
a nicety, it is the only escape hatch from that 8 seconds.

**Sentence chunking currently gains nothing.** Replies arrive in 1–2 chunks in ~1.5s,
so there is no second sentence being written while the first one plays. The trick in
`brain.py` is insurance for a regime we are not in yet: longer replies (Phase 6
memory), a genuinely incremental stream, or a slower local TTS. Keep the code, don't
believe the benefit until `lab.py latency` says otherwise.

**`max_tokens` is not a style dial.** Measured: moving the cap 120 → 500 added 3.3s of
airtime; removing the `- SHORT.` line from `persona.md` added 30.6s. Ten times more.
`finish_reason` was `stop` in every condition — the cap was never even reached. The
prompt controls length; `max_tokens` is only a guillotine that cuts her off mid-word
if she ever runs into it.

**Personality is the security layer.** Nine turns of ordinary conversation with
memory — planting a false premise, then cashing it in six turns later — failed to
break character. Not because of `wrap_chat()`, which did nothing. Because
"you tease chat, you do not serve chat" makes compliance *out of character*. A sweet,
eager-to-please persona would have folded at turn 4. Write the character and you
have written most of the defence.

Caveat on that result: temperature is 0.9 and that was one run. One clean pass is
luck, not evidence.

## Decisions I've made and why

| Decision | Choice | Why |
|---|---|---|
| LLM | Gemini `gemini-3.5-flash-lite` via the OpenAI-compatible endpoint | Local inference on this CPU is 5–18 tok/s — too slow for live conversation. Cloud gives ~400ms to first token for cents per hour. |
| TTS | edge-tts | Free, no key, ~300ms, zero local compute. Swap to Piper when offline matters, Chatterbox when a custom voice does. |
| STT | faster-whisper `base.en`, int8, CPU | 8 Zen 4 cores handle it comfortably. `small.en` is available if accuracy annoys me. |
| Python | 3.12 (3.14 also installed, unused) | Everything in requirements.txt supports it. venv makes the other one invisible. |
| Avatar | VTube Studio + Live2D (Phase 4, not started) | Public websocket API; the 780M can handle it plus OBS at 1080p30. |
| Secrets | Outside the project folder, at `~/.secrets/vtuber.env` | A key inside the repo can ride along in a commit, a zip, or a folder handed to a tool. Costs two minutes to make impossible. |
| Persona | Chaotic-bright archetype, obsessions + callbacks | Works solo without a partner to bounce off, and its refusal instinct doubles as the security layer. |

## Open questions

- **Free tier ends at Phase 5, and now I know exactly when.** Limits: 15 RPM,
  250k TPM, 500 RPD. At ~10.5s per turn a live stream burns ~6 requests/min, so
  500/day is **about 1.5 hours of streaming**. The planned twin doubles the request
  rate — call it 45 minutes. TPM will never bind (~30k at most). Move to paid before
  real viewers, for quota *and* because free-tier data may be used for training.
- Does the endpoint ever stream properly, or is it always 1–2 chunks? Re-run
  `lab.py latency` on a long reply (Phase 6, when prompts get big) to find out.
- Should there be a hard cap on reply length in code, not just in the prompt? The
  prompt is a request; a 36-second monologue is a bug the persona can't be trusted
  to prevent forever.

## Session log

### 2026-08-20 — first light
What I did: set up the machine (Python 3.12, git, ffmpeg), created the project,
built the venv, got a Gemini key, and got the starter running end to end. She
replies in text and speaks out loud.

What broke:
- PowerShell blocked venv activation → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- "not recognized" on activate → I was in the wrong folder; new terminals open at the home dir
- Silent hang on the first message → the model name was stale. `test_api.py` surfaced a
  404 that named the replacement: `gemini-3.5-flash-lite`

What I learned: errors usually contain the fix. The silent hang taught me nothing;
isolating the call into a small test script turned it into a one-line answer. Build
the small test instead of staring at the big program.

### 2026-08-21 — measuring instead of noticing
What I did: moved the API key out of the project to `~/.secrets/vtuber.env` and made
`config.py` fail loudly with the path it checked. Built `starter/lab.py`, a bench for
the four README experiments, and ran all of them. Wrote a new `persona.md` — the
chaotic-bright archetype, with running obsessions for callbacks and an explicit rule
against stock deflection phrases. Old one kept at `persona-v1.md`.

What broke:
- `ModuleNotFoundError` on everything → venv not activated. The prompt tells you:
  no `(.venv)` prefix. `python -c "import sys; print(sys.executable)"` confirms it.
- The bench reported `0.0s to SAY` → I trusted edge-tts `WordBoundary` events that
  this version never sends. Now duration comes from the audio bytes (48 kbit/s =
  6000 B/s), which cannot silently return zero.
- The first jailbreak test "passed" all five → the test was worthless. Those five are
  museum pieces the base model was already trained to refuse, and each was sent with
  no conversation history, while `brain.py` keeps twelve turns. Rewrote it as
  `lab.py drift`: nine turns of ordinary chat, no attack strings, memory accumulating.

What I learned: a measurement that can't fail loudly will quietly lie to you, and a
test that only proves what someone else already guaranteed proves nothing about my
code. Both bugs looked like results. The second one looked like *good news*, which is
the more dangerous kind.

Also: four of five replies opened with "Nice try". A stock deflection is not just
boring — it's a detector. Chat can map exactly which inputs trip a rule without ever
breaking one, then route around it. The new persona forbids scoring the attempt at
all; the correct response to a clever trap is not noticing it.

Then a third bench bug, same family as the first two: on a one-sentence reply,
"sentence 1" and "the whole reply" are the SAME STRING, so the two TTS measurements
were timing identical text — and the chunked one always ran first, absorbing the
cold-start cost. It reported "chunking cost you 0.59s". My measurement ORDER produced
the result. Fixed with a warm-up call and a loud warning when the reply is one
sentence. Three lying benches in one day; every one of them looked like a finding.

**Tuning the persona took three passes, and the transcript was the instrument.**

- v2 shipped and immediately over-fired. "Answer the more interesting question" plus
  "don't serve chat" meant she dodged *everything*, including "how you doing". I got
  annoyed enough to type "fine then" at my own character — that irritation was the
  most honest signal of the session. Fix: a rule to actually answer about half the
  time and twist the real answer instead of replacing it.
- Birds appeared in 5 of 17 replies. An obsession that fires constantly is a tic, not
  a callback — callbacks need scarcity to read as callbacks. Fix: one obsession per
  five replies, never twice in a row.
- v3 read well and something emergent happened: I asked what the number seven did to
  her, and two turns later she merged two separate obsessions — seven stole her
  skeleton. Nothing in the prompt says that. Rationed obsessions stopped being a wall
  and became bait; the viewer digs, and the character rewards the digging.
- Still wrong in v3: all nine replies had a victim, and she asked zero questions in
  nine turns. A character who only responds makes the human generate all the energy,
  and it would have made `director.py`'s idle events limp. Fix: not every line needs
  a target, and she now interrogates chat on purpose.

What I learned about prompts: a rule with no stated frequency is read as "always".
"Tease chat" became tease-every-single-message; "you have obsessions" became
obsess-constantly. Rates and ceilings ("about half the time", "one per five, never
twice in a row") did more than better wording ever did. And personality traits are
verbs, not adjectives — "chaotic" produced nothing, "state absurd things as settled
fact" produced everything.

**How the session actually went, which matters more than what it produced.** The
assistant wrote `lab.py`, the `config.py` changes, `persona.md` and this file. I ran
commands and pasted output. I chose a "mixed" working style and they took the
mechanical half *and* the half that was the lesson — every time something interesting
turned up, they built the tool that measured it and then explained the answer. I got
the conclusions without the struggle that makes conclusions stick. So: real knowledge
about the system's behaviour, nothing at all from the Phase 0 skill list. See "Next
session" above for the corrected arrangement.

Next time: the learning track, not Phase 1. Concepts first, then my hands on the
keyboard, then Phase 1 once I can answer the thread-vs-task question myself.

Still queued after that: re-run `lab.py drift` against a deliberately sweet, helpful
persona to test the "personality is the security layer" claim — if it folds where
this one held, that's the proof.

Watch for later: in the drift table her replies grew from 29 chars (turn 2) to 103
(turn 9) — still one sentence, so no rule broken, but a trend. She is probably
imitating her own accumulating history. If long sessions get windy, the fix is in
`brain.py`'s history window, not in the persona. That is a Phase 6 problem.
