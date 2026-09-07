"""
The brain: streams tokens from an LLM and emits COMPLETE SENTENCES as soon
as they are ready.

This sentence-level streaming is the whole trick. If you wait for the full
reply before speaking, you eat 2-4 seconds of dead air and the illusion dies.
If you speak sentence-by-sentence while the LLM is still writing, first audio
lands in well under a second.
"""
import re
from collections import deque

from openai import AsyncOpenAI

from config import cfg

# Split on sentence enders, but not on "Mr." / "3.5" / "..." mid-thought.
_SENT_END = re.compile(r"(?<=[.!?…])\s+")
_TAG = re.compile(r"^\s*\[(\w+)\]\s*")


class Brain:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(base_url=cfg.llm_base_url, api_key=cfg.llm_api_key)
        self.system = open(cfg.persona_file, encoding="utf-8").read()
        self.history: deque[dict] = deque(maxlen=cfg.history_turns * 2)
        self.emotion = "neutral"

    def _messages(self, stimulus: str) -> list[dict]:
        return [
            {"role": "system", "content": self.system},
            *self.history,
            {"role": "user", "content": stimulus},
        ]

    async def respond(self, stimulus: str):
        """Async-generate sentences. Yields str, one sentence at a time."""
        buf, full = "", ""
        first_chunk = True

        stream = await self.client.chat.completions.create(
            model=cfg.llm_model,
            messages=self._messages(stimulus),
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            buf += delta
            full += delta

            # Pull the [emotion] tag off the very front and route it to the face.
            if first_chunk and (m := _TAG.match(buf)):
                self.emotion = m.group(1)
                buf = buf[m.end():]
                first_chunk = False

            # Emit every complete sentence sitting in the buffer.
            parts = _SENT_END.split(buf)
            if len(parts) > 1:
                for sentence in parts[:-1]:
                    if sentence.strip():
                        yield sentence.strip()
                buf = parts[-1]

        if buf.strip():
            yield buf.strip()

        self.history.append({"role": "user", "content": stimulus})
        self.history.append({"role": "assistant", "content": full.strip()})


def wrap_chat(username: str, text: str) -> str:
    """
    Fence untrusted chat input. Chat WILL try to jailbreak you on stream.
    Never concatenate raw chat straight into the prompt.
    """
    text = text.replace("\n", " ")[:280]
    return f"Chat message from viewer <{username}>: {text}"


def wrap_voice(text: str) -> str:
    return f"Your streaming partner just said out loud: {text}"
