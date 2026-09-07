"""
The voice: text in, audio out of the speakers, with a queue so sentences
play back-to-back while the brain is still generating the next one.

Default backend is edge-tts: free, no API key, ~200-400ms to first audio.
It is a fine place to start and a bad place to finish - you cannot clone a
voice with it. See the roadmap for where to go next (Chatterbox / GPT-SoVITS
for a custom voice, Kokoro for speed).

Playback goes through ffplay so we don't need a native audio decoder.
Install ffmpeg first:  https://ffmpeg.org/download.html
"""
import asyncio
import shutil

import edge_tts

from config import cfg

if shutil.which("ffplay") is None:
    raise SystemExit("ffplay not found. Install ffmpeg and put it on your PATH.")


class Voice:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.speaking = asyncio.Event()
        self._cancel = False
        # Rough loudness signal (0.0-1.0) other components can read for lip sync.
        self.level = 0.0

    async def say(self, sentence: str) -> None:
        await self.queue.put(sentence)

    def interrupt(self) -> None:
        """Drop everything queued. Called when the human starts talking."""
        self._cancel = True
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def run(self) -> None:
        """Consume the queue forever. Run this as a background task."""
        while True:
            sentence = await self.queue.get()
            if sentence is None:
                return
            self._cancel = False
            try:
                await self._speak(sentence)
            except Exception as e:  # a dead TTS call must not kill the stream
                print(f"[voice] error: {e}")

    async def _speak(self, sentence: str) -> None:
        self.speaking.set()
        comm = edge_tts.Communicate(
            sentence, cfg.tts_voice, rate=cfg.tts_rate, pitch=cfg.tts_pitch
        )
        proc = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", "pipe:0",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            async for chunk in comm.stream():
                if self._cancel:
                    break
                if chunk["type"] == "audio":
                    proc.stdin.write(chunk["data"])
                    self.level = 1.0
            if proc.stdin:
                proc.stdin.close()
            if self._cancel:
                proc.kill()
            await proc.wait()
        finally:
            self.level = 0.0
            self.speaking.clear()
