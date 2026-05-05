from __future__ import annotations

import argparse
import asyncio
import wave
from io import BytesIO
from types import MethodType

from sovits_wyoming_connector.handler import SovitsEventHandler


class FakeSovitsClient:
    def __init__(self, wav_bytes: bytes) -> None:
        self.wav_bytes = wav_bytes
        self.texts: list[str] = []

    async def synthesize_wav(self, text: str) -> bytes:
        self.texts.append(text)
        return self.wav_bytes


def make_wav() -> bytes:
    wav_io = BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x01\x02" * 3)
    return wav_io.getvalue()


def make_handler(client: FakeSovitsClient) -> tuple[SovitsEventHandler, list[str]]:
    handler = object.__new__(SovitsEventHandler)
    handler.cli_args = argparse.Namespace(samples_per_chunk=2)
    handler.sovits_client = client
    event_types: list[str] = []

    async def write_event(self: SovitsEventHandler, event) -> None:
        event_types.append(event.type)

    handler.write_event = MethodType(write_event, handler)
    return handler, event_types


def test_synthesize_text_writes_wyoming_audio_events() -> None:
    client = FakeSovitsClient(make_wav())
    handler, event_types = make_handler(client)

    asyncio.run(handler._synthesize_text("hello\nworld"))

    assert client.texts == ["hello world"]
    assert event_types == [
        "audio-start",
        "audio-chunk",
        "audio-chunk",
        "audio-stop",
    ]
