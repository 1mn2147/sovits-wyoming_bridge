"""Audio helpers for converting WAV responses into Wyoming chunks."""

from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from io import BytesIO


@dataclass(frozen=True)
class PcmAudio:
    """Decoded PCM audio data from a WAV container."""

    rate: int
    width: int
    channels: int
    audio: bytes


def wav_bytes_to_pcm(wav_bytes: bytes) -> PcmAudio:
    """Decode WAV bytes into PCM attributes and raw audio bytes."""

    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        return PcmAudio(
            rate=wav_file.getframerate(),
            width=wav_file.getsampwidth(),
            channels=wav_file.getnchannels(),
            audio=wav_file.readframes(wav_file.getnframes()),
        )


def iter_pcm_chunks(audio: PcmAudio, samples_per_chunk: int) -> list[bytes]:
    """Split PCM audio on sample boundaries."""

    if samples_per_chunk <= 0:
        raise ValueError("samples_per_chunk must be greater than zero")

    bytes_per_sample = audio.width * audio.channels
    bytes_per_chunk = bytes_per_sample * samples_per_chunk
    num_chunks = int(math.ceil(len(audio.audio) / bytes_per_chunk))

    return [
        audio.audio[offset : offset + bytes_per_chunk]
        for offset in range(0, num_chunks * bytes_per_chunk, bytes_per_chunk)
        if audio.audio[offset : offset + bytes_per_chunk]
    ]
