# AI VTuber — life project

Everything for building a Neuro-sama-style AI character. Started August 2026.

**Machine:** Lenovo IdeaPad Slim 5, Windows, no discrete GPU.
**Strategy:** cloud LLM for the brain, everything else local on CPU.
See `starter/LAPTOP-SETUP.md` for why and what that means concretely.

## What's here

| | |
|---|---|
| `roadmap.html` | The 9-phase plan. **Open this in a browser.** Tick boxes as you go; progress saves in the browser. |
| `PROGRESS.md` | Your log. Update it at the end of every session — this is what carries context into a new chat. |
| `starter/` | A ~400-line working prototype of the whole pipeline. Read `starter/README.md`. |

## Start here

1. Open `roadmap.html`, read "What you are actually building" and the latency section.
2. Read `starter/LAPTOP-SETUP.md` — the CPU-only stack, and why.
3. Finish the machine setup (Python 3.12, git, ffmpeg).
4. Follow `starter/README.md` to get her talking.

## Setup checklist

- [x] Python 3.12 installed — every package in `requirements.txt` supports it. Leave it alone.
- [x] Git installed (`winget install Git.Git`)
- [x] ffmpeg installed (`winget install Gyan.FFmpeg`)
- [x] Reopened PowerShell; `python --version`, `git --version`, `ffmpeg -version` all work
- [x] Virtual environment created in `starter/`
- [x] `requirements.txt` installed
- [x] API key obtained and put in `starter/.env` (copied from `.env.example`)
- [x] `python main.py` — she replies

## Rules for this project

- **Never put an API key anywhere but `.env`.** Not in code, not in chat, not in git.
  `.gitignore` already excludes it.
- **Update `PROGRESS.md` before you close a session.** Future you has no memory either.
- **One chat per phase.** Paste `PROGRESS.md` in as the first message.
- **Plugged in, Best Performance power mode** whenever you're running the pipeline.

## Where the data goes

The pipeline sends whatever it reacts to — your voice transcripts, and later real
viewers' chat messages — to whichever LLM provider is configured in `starter/.env`.
Nothing leaves the machine until you set a key. Worth remembering before Phase 5,
when strangers' messages start flowing through it.
