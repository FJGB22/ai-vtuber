"""
The director: decides WHAT she reacts to and WHEN she talks.

Nobody warns you about this part, and it is the difference between an AI
VTuber and a chatbot with a wig. A live stream produces far more stimuli
than she can answer - chat spam, your voice, game events, silence. Something
has to arbitrate. That something is here.

Rules, in priority order:
  1. Your voice always wins (she is talking WITH you, not AT chat).
  2. Otherwise pick one chat message from the recent batch, biased toward
     messages that mention her by name.
  3. If nothing happens for a while, say something unprompted. Dead air is
     the number one thing that makes a stream feel like a demo.
"""
import random
import time
from dataclasses import dataclass, field

IDLE_SECONDS = 25.0


@dataclass(order=True)
class Event:
    priority: int
    ts: float = field(compare=False)
    kind: str = field(compare=False)  # "voice" | "chat" | "idle"
    text: str = field(compare=False)
    author: str = field(compare=False, default="")


class Director:
    def __init__(self, char_name: str) -> None:
        self.char_name = char_name.lower()
        self.chat_buffer: list[Event] = []
        self.pending_voice: Event | None = None
        self.last_spoke = time.time()

    def push_chat(self, author: str, text: str) -> None:
        self.chat_buffer.append(Event(2, time.time(), "chat", text, author))
        self.chat_buffer = self.chat_buffer[-50:]  # never let it grow forever

    def push_voice(self, text: str) -> None:
        self.pending_voice = Event(0, time.time(), "voice", text)

    def next_event(self) -> Event | None:
        if self.pending_voice:
            ev, self.pending_voice = self.pending_voice, None
            self.chat_buffer.clear()  # chat from 30s ago is stale, drop it
            self.last_spoke = time.time()
            return ev

        if self.chat_buffer:
            # Weight messages that say her name much higher.
            weights = [
                5.0 if self.char_name in e.text.lower() else 1.0
                for e in self.chat_buffer
            ]
            ev = random.choices(self.chat_buffer, weights=weights, k=1)[0]
            self.chat_buffer.clear()
            self.last_spoke = time.time()
            return ev

        if time.time() - self.last_spoke > IDLE_SECONDS:
            self.last_spoke = time.time()
            return Event(
                9, time.time(), "idle",
                "Nobody has said anything for a while. Say something unprompted "
                "to fill the silence - a thought, a complaint, a callback.",
            )
        return None
