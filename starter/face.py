"""
The face: drives a Live2D model in VTube Studio over its websocket API.

Optional for day 1 - set VTS_ENABLED=true once you have a model loaded.

VTube Studio does mouth movement itself from your system audio if you point
its microphone-lipsync at an audio loopback device (VB-Cable on Windows,
BlackHole on macOS). That is far easier than driving mouth params yourself,
so this file only handles EXPRESSIONS - the emotion tag from the brain.

Setup in VTube Studio: Settings -> Start API (port 8001). Then in the model's
hotkey settings create hotkeys literally named happy / sad / smug / etc.
"""
import json

import websockets

from config import cfg

PLUGIN = {
    "pluginName": "AIVTuberStarter",
    "pluginDeveloper": "you",
}


class Face:
    def __init__(self) -> None:
        self.ws = None
        self.token = None
        self.hotkeys: dict[str, str] = {}

    async def connect(self) -> None:
        self.ws = await websockets.connect(cfg.vts_url)
        await self._auth()
        await self._load_hotkeys()

    async def _send(self, message_type: str, data: dict | None = None) -> dict:
        await self.ws.send(json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": message_type,
            "messageType": message_type,
            "data": data or {},
        }))
        return json.loads(await self.ws.recv())

    async def _auth(self) -> None:
        # First run pops a confirmation dialog inside VTube Studio. Click allow.
        r = await self._send("AuthenticationTokenRequest", PLUGIN)
        self.token = r["data"]["authenticationToken"]
        await self._send(
            "AuthenticationRequest", {**PLUGIN, "authenticationToken": self.token}
        )

    async def _load_hotkeys(self) -> None:
        r = await self._send("HotkeysInCurrentModelRequest")
        for hk in r["data"]["availableHotkeys"]:
            self.hotkeys[hk["name"].strip().lower()] = hk["hotkeyID"]

    async def set_emotion(self, emotion: str) -> None:
        hk = self.hotkeys.get(emotion.lower())
        if hk:
            await self._send("HotkeyTriggerRequest", {"hotkeyID": hk})
