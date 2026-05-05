#!/usr/bin/env python3
"""Smoke test for Wyoming TTS servers."""

from __future__ import annotations

import argparse
import asyncio

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient
from wyoming.error import Error
from wyoming.info import Describe, Info
from wyoming.tts import Synthesize


async def run(args: argparse.Namespace) -> int:
    audio_bytes = 0
    audio_chunks = 0
    saw_audio_start = False
    saw_audio_stop = False

    async with AsyncClient.from_uri(args.uri) as client:
        await client.write_event(Describe().event())
        info_event = await asyncio.wait_for(client.read_event(), timeout=args.timeout)
        if info_event is None or not Info.is_type(info_event.type):
            raise RuntimeError("No Wyoming info response")

        await client.write_event(Synthesize(text=args.text).event())

        while True:
            event = await asyncio.wait_for(client.read_event(), timeout=args.timeout)
            if event is None:
                raise RuntimeError("Connection closed before synthesis completed")

            if Error.is_type(event.type):
                err = Error.from_event(event)
                print(f"ERROR: code={err.code} message={err.text}")
                return 2

            if AudioStart.is_type(event.type):
                saw_audio_start = True
                start = AudioStart.from_event(event)
                print(
                    f"AUDIO_START: rate={start.rate} width={start.width} "
                    f"channels={start.channels}"
                )
                continue

            if AudioChunk.is_type(event.type):
                chunk = AudioChunk.from_event(event)
                audio_chunks += 1
                audio_bytes += len(chunk.audio)
                continue

            if AudioStop.is_type(event.type):
                saw_audio_stop = True
                break

    if saw_audio_start and saw_audio_stop and audio_chunks > 0:
        print(f"OK: chunks={audio_chunks} bytes={audio_bytes}")
        return 0

    raise RuntimeError("Synthesis finished without complete audio stream")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="tcp://127.0.0.1:10200")
    parser.add_argument("--text", default="Wyoming connector smoke test")
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser.parse_args()


def main() -> None:
    raise SystemExit(asyncio.run(run(parse_args())))


if __name__ == "__main__":
    main()
