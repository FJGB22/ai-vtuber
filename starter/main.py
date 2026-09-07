"""
Wire everything together.

    python main.py            # keyboard "chat" only, no mic needed
    python main.py --mic      # also listen to your microphone

Type into the terminal to act as a chat viewer. Ctrl-C to stop.
"""
import argparse
import asyncio
import sys
import threading

from brain import Brain, wrap_chat, wrap_voice
from config import cfg
from director import Director
from voice import Voice


async def keyboard_feed(director: Director) -> None:
    """Stand-in for Twitch chat. Swap this out in Phase 5."""
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            return
        line = line.strip()
        if line:
            director.push_chat("you_in_chat", line)


async def think_loop(brain: Brain, voice: Voice, director: Director, face) -> None:
    while True:
        event = director.next_event()
        if event is None:
            await asyncio.sleep(0.15)
            continue

        if event.kind == "chat":
            stimulus = wrap_chat(event.author, event.text)
        elif event.kind == "voice":
            stimulus = wrap_voice(event.text)
        else:
            stimulus = event.text

        print(f"\n  << [{event.kind}] {event.author or ''} {event.text[:70]}")
        print(f"  >> {cfg.char_name}: ", end="", flush=True)

        async for sentence in brain.respond(stimulus):
            print(sentence, end=" ", flush=True)
            await voice.say(sentence)

        if face:
            await face.set_emotion(brain.emotion)
        print()


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mic", action="store_true", help="listen to the microphone")
    args = ap.parse_args()

    brain, voice, director = Brain(), Voice(), Director(cfg.char_name)

    face = None
    if cfg.vts_enabled:
        from face import Face
        face = Face()
        await face.connect()
        print("[face] connected to VTube Studio")

    if args.mic:
        from ears import Ears
        loop = asyncio.get_running_loop()

        async def on_speech(text: str) -> None:
            voice.interrupt()          # she stops talking the moment you start
            director.push_voice(text)

        ears = Ears(loop, on_speech)
        threading.Thread(target=ears.run, daemon=True).start()
        print("[ears] microphone live")

    print(f"[ready] {cfg.char_name} is live. Type to act as chat.\n")

    await asyncio.gather(
        voice.run(),
        keyboard_feed(director),
        think_loop(brain, voice, director, face),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nstream ended")
