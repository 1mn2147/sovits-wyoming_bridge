"""Wyoming event handler."""

from __future__ import annotations

import argparse
import logging

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler
from wyoming.tts import (
    Synthesize,
    SynthesizeChunk,
    SynthesizeStart,
    SynthesizeStop,
    SynthesizeStopped,
)

from .audio import iter_pcm_chunks, wav_bytes_to_pcm
from .sovits_client import SovitsClient

_LOGGER = logging.getLogger(__name__)


class SovitsEventHandler(AsyncEventHandler):
    """Handle Wyoming TTS events and proxy synthesis to GPT-SoVITS."""

    def __init__(
        self,
        wyoming_info: Info,
        cli_args: argparse.Namespace,
        sovits_client: SovitsClient,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.wyoming_info_event = wyoming_info.event()
        self.cli_args = cli_args
        self.sovits_client = sovits_client
        self._stream_voice = None
        self._stream_chunks: list[str] = []
        self._is_streaming = False

    async def handle_event(self, event: Event) -> bool:
        """Handle one Wyoming event."""

        try:
            if Describe.is_type(event.type):
                await self.write_event(self.wyoming_info_event)
                return True

            if SynthesizeStart.is_type(event.type):
                stream_start = SynthesizeStart.from_event(event)
                self._is_streaming = True
                self._stream_voice = stream_start.voice
                self._stream_chunks = []
                return True

            if SynthesizeChunk.is_type(event.type):
                stream_chunk = SynthesizeChunk.from_event(event)
                self._stream_chunks.append(stream_chunk.text)
                return True

            if SynthesizeStop.is_type(event.type):
                text = "".join(self._stream_chunks)
                self._is_streaming = False
                await self._synthesize_text(text)
                await self.write_event(SynthesizeStopped().event())
                return True

            if Synthesize.is_type(event.type):
                if self._is_streaming:
                    return True

                synthesize = Synthesize.from_event(event)
                await self._synthesize_text(synthesize.text)
                return True

            return True
        except Exception as err:
            _LOGGER.exception("Error handling Wyoming event")
            await self.write_event(
                Error(text=str(err), code=err.__class__.__name__).event()
            )
            return True

    async def _synthesize_text(self, text: str) -> None:
        """Synthesize text and write Wyoming audio events."""

        normalized_text = " ".join(text.strip().splitlines())
        if not normalized_text:
            await self.write_event(AudioStop().event())
            return

        _LOGGER.info("Synthesizing %d characters", len(normalized_text))
        wav_bytes = await self.sovits_client.synthesize_wav(normalized_text)
        pcm_audio = wav_bytes_to_pcm(wav_bytes)

        await self.write_event(
            AudioStart(
                rate=pcm_audio.rate,
                width=pcm_audio.width,
                channels=pcm_audio.channels,
            ).event()
        )

        for chunk in iter_pcm_chunks(pcm_audio, self.cli_args.samples_per_chunk):
            await self.write_event(
                AudioChunk(
                    audio=chunk,
                    rate=pcm_audio.rate,
                    width=pcm_audio.width,
                    channels=pcm_audio.channels,
                ).event()
            )

        await self.write_event(AudioStop().event())
