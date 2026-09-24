"""
The ears: microphone -> voice-activity detection -> Whisper -> text events.

The VAD here is a deliberately dumb energy gate so you can read it in one
sitting and understand what a VAD actually does. Replace it with Silero VAD
(torch.hub 'snakers4/silero-vad') the moment you have background noise.
"""
import asyncio
import queue
import threading

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import cfg


class Ears:
    def __init__(self, loop: asyncio.AbstractEventLoop, on_speech) -> None:
        self.loop = loop
        self.on_speech = on_speech  # async callable(text)
        self.model = WhisperModel(
            cfg.whisper_model, device=cfg.whisper_device, compute_type="int8"
        )
        self._frames: queue.Queue[np.ndarray] = queue.Queue()
        self.speech_started = threading.Event()

    def _callback(self, indata, frames, time_info, status):
        self._frames.put(indata.copy())

    def run(self) -> None:
        """Blocking. Run this in a worker thread."""
        block = int(cfg.sample_rate * 0.1)  # 100ms blocks
        buffer: list[np.ndarray] = []
        silent_blocks = 0
        needed_silence = int(cfg.vad_silence_sec / 0.1)

        with sd.InputStream(
            samplerate=cfg.sample_rate, channels=1, dtype="float32",
            blocksize=block, callback=self._callback,
        ):
            while True:
                chunk = self._frames.get()
                rms = float(np.sqrt(np.mean(chunk**2)))
                loud = rms > cfg.vad_threshold

                if loud:
                    if not buffer:
                        self.speech_started.set()  # -> main loop interrupts TTS
                    buffer.append(chunk)
                    silent_blocks = 0
                elif buffer:
                    buffer.append(chunk)
                    silent_blocks += 1
                    if silent_blocks >= needed_silence:
                        audio = np.concatenate(buffer).flatten()
                        buffer, silent_blocks = [], 0
                        self.speech_started.clear()
                        if len(audio) > cfg.sample_rate * 0.4:  # ignore coughs
                            self._transcribe(audio)

    def _transcribe(self, audio: np.ndarray) -> None:
        segments, _ = self.model.transcribe(audio, language="en", beam_size=1)
        text = " ".join(s.text for s in segments).strip()
        if len(text) > 2:
            asyncio.run_coroutine_threadsafe(self.on_speech(text), self.loop)
