from __future__ import annotations

import wave
from io import BytesIO

from sovits_wyoming_connector.audio import iter_pcm_chunks, wav_bytes_to_pcm


def make_wav() -> bytes:
    wav_io = BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x01\x02" * 5)
    return wav_io.getvalue()


def test_wav_bytes_to_pcm() -> None:
    pcm = wav_bytes_to_pcm(make_wav())

    assert pcm.rate == 16000
    assert pcm.width == 2
    assert pcm.channels == 1
    assert pcm.audio == b"\x01\x02" * 5


def test_iter_pcm_chunks_respects_sample_boundaries() -> None:
    pcm = wav_bytes_to_pcm(make_wav())

    chunks = iter_pcm_chunks(pcm, samples_per_chunk=2)

    assert chunks == [b"\x01\x02" * 2, b"\x01\x02" * 2, b"\x01\x02"]
