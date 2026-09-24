# Running this on a laptop with no GPU

Written for a Lenovo IdeaPad Slim 5 (integrated graphics), but it applies to any
thin-and-light without a discrete NVIDIA card.

## Your actual machine (measured 2026-08-20)

| | |
|---|---|
| CPU | AMD Ryzen 7 8845HS — 8 cores / 16 threads, Zen 4 |
| iGPU | Radeon 780M |
| RAM | 16 GB (~13.8 GB usable; the rest is reserved for the iGPU) |
| Disk | ~284 GB free |
| Python | 3.12.10 and 3.14 both installed — **this project uses 3.12** |

This is a much stronger machine than "no GPU" suggests, and it changes three things:

- **Whisper:** use `base.en`, not `tiny.en`. `small.en` is also within reach if you want
  better accuracy. Eight Zen 4 cores handle it comfortably.
- **Local LLMs are a real fallback,** just not for live conversation — see below.
- **Phase 4–5 will be fine.** The 780M is among the best integrated GPUs made. VTube Studio
  plus OBS at 1080p30 with AMF hardware encoding is realistic, not a stretch.

**RAM is your tightest resource, not the CPU.** 13.8 GB usable means: don't run a local
LLM, OBS, VTube Studio and a game at the same time. Something has to be in the cloud, and
the LLM is the right thing to move there.

### Two Pythons — always be explicit

`py --list` shows 3.14 as the default and 3.12 as the second. `python` resolves to 3.12.
Rather than rely on that, create the virtual environment explicitly:

```powershell
py -3.12 -m venv .venv
```

Once `.venv` is activated, `python` and `pip` unambiguously mean 3.12 and the question
disappears. That is the entire point of a virtual environment.

## The short version

**Put the brain in the cloud, keep everything else local.** On this machine a cloud
LLM is not the compromise — it is genuinely the faster option, and it costs single-digit
cents per hour. Everything else in the pipeline runs fine on your CPU.

| Component | On your laptop | Why |
|---|---|---|
| **Brain (LLM)** | Cloud API | CPU inference is 5–20× too slow for live conversation |
| **Voice (TTS)** | `edge-tts` now → Piper later | Piper is ~30× realtime on CPU, ~300 MB RAM |
| **Ears (STT)** | `faster-whisper` `tiny.en` or `base.en`, int8 | Runs comfortably on CPU for short utterances |
| **Face (Live2D)** | Works, but this is your bottleneck | 2D rendering + OBS encoding on an iGPU |

## Why not a local LLM

Measured ranges for your class of hardware (8845HS + DDR5), Q4/Q5 quantised:

| Setup | tokens/sec | 120-token reply |
|---|---|---|
| 7B on CPU only | ~5–10 | 12–24 s |
| 7B on the 780M via llama.cpp **Vulkan** | ~12–18 | 7–10 s |
| Llama 3.1 8B Q5 on the 780M | ~8–14 | 9–15 s |
| 3B on CPU | ~20–35 | 4–6 s |

Note the Vulkan row — offloading to the 780M roughly doubles CPU-only throughput, and it
is worth knowing about for later. But even the best row here is far too slow for live
conversation. The limit is memory bandwidth (~80–86 GB/s on dual-channel DDR5), not your
core count, so no amount of CPU tuning fixes it.

Where local *does* make sense on this machine: experimenting offline, testing persona
changes without burning API calls, and running a 3B model when you have no internet.
Set that up in Phase 6, not now.

Sentence streaming saves you a lot of that — you only need the *first sentence*, maybe
15 tokens — but prompt processing on CPU is the real killer. A 1,000-token persona has
to be re-read before a single token comes out, and on CPU that alone can cost seconds.

A cloud API gives you time-to-first-token in the 300–600 ms range with no fan noise, no
thermal throttling, and no 5 GB of RAM gone. Use one.

**Cost math for a 1-hour stream:** roughly one reply every 10 seconds is ~360 replies.
At ~1,200 input tokens (persona + history) and ~100 output tokens each, that's ~430K
input + ~36K output tokens per hour. On any of the cheap fast tiers (Gemini Flash-Lite,
GPT-mini, Claude Haiku class) that lands around **5–15 cents an hour**. Check current
pricing pages — it moves — but the order of magnitude is stable.

Set it in `.env`:

```bash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/   # or OpenAI's
LLM_API_KEY=your-key
LLM_MODEL=gemini-2.5-flash-lite
```

Keep `max_tokens` at 120 or lower in `config.py`. On a budget model this matters twice
over: latency *and* your bill.

## Ears: use the small Whisper

In `.env`:

```bash
WHISPER_MODEL=tiny.en     # start here; move to base.en if accuracy annoys you
WHISPER_DEVICE=cpu
```

`compute_type="int8"` is already set in `ears.py` — that is what makes CPU Whisper viable.
If it still feels sluggish, switch to `sherpa-onnx`, which is built for exactly this case.

## Voice: edge-tts now, Piper when you want it local

`edge-tts` is the default and needs nothing from your CPU — it's a network call. Fine
for months.

When you want the voice to work offline, **Piper** is the CPU answer: around 30× realtime,
~40 ms to first audio, ~300 MB RAM. It sounds a bit robotic, which is a real trade —
Kokoro sounds noticeably better for ~900 MB and roughly 3× the compute, still fine on CPU.

```bash
pip install piper-tts
python -m piper.download_voices en_US-lessac-medium
```

Then swap the body of `Voice._speak()` to pipe Piper's raw PCM into `ffplay` instead of
edge-tts's mp3 stream. Repo: <https://github.com/OHF-Voice/piper1-gpl>

Voice *cloning* (Chatterbox, GPT-SoVITS, XTTS) is the one thing genuinely off the table
on CPU — XTTS alone wants ~4.5 GB and 600 ms latency. Rent a GPU by the hour for that,
or use a paid cloud voice.

## Where the laptop actually hurts

Phases 0–3 — foundations, brain, voice, ears — are completely fine here. You have months
of work that this machine handles without complaint.

Phase 4–5 is the squeeze: VTube Studio rendering a Live2D model, OBS encoding a stream,
and possibly a game, all on integrated graphics. It does run. To make it survive:

- Stream at **720p30**, not 1080p60.
- Use **hardware encoding** in OBS (QuickSync on Intel, AMF/VCE on AMD), never x264.
- Expect thermal throttling in a chassis this thin. Elevate it, watch your clocks.
- Close the browser. Chrome will eat the RAM you need.

## Do not buy anything yet

You are months away from the phase where hardware matters, and by then you will know
exactly what is slow, which is a much better basis for spending money. When you get there
the options are, in order of sanity:

1. **Keep using cloud APIs for everything.** A GPU is not a requirement for this project —
   it was Vedal's choice, not a law of nature.
2. **Rent a cloud GPU by the hour** for fine-tuning and voice cloning specifically. You need
   it in bursts, not continuously.
3. **Build a cheap desktop** with a used 12–16 GB NVIDIA card. Only worth it once you are
   streaming regularly and the API bill has become a real number.

## Check what you're working with

```bash
# Windows PowerShell
Get-CimInstance Win32_Processor | Select Name, NumberOfCores
Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum
```

16 GB of RAM makes all of the above comfortable. 8 GB is workable if you stay on cloud
APIs and `tiny.en`, but you will be closing Chrome a lot.
