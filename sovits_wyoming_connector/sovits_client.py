"""HTTP client for GPT-SoVITS."""

from __future__ import annotations

import json

import aiohttp

from .config import SovitsConfig


class SovitsClient:
    """Small async client for the GPT-SoVITS `/tts` endpoint."""

    def __init__(self, config: SovitsConfig) -> None:
        self.config = config

    async def synthesize_wav(self, text: str) -> bytes:
        """Synthesize text and return WAV bytes."""

        clean_text = " ".join(text.strip().splitlines())
        if not clean_text:
            raise ValueError("Text is empty")

        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.config.url,
                json=self.config.build_payload(clean_text),
            ) as response:
                response_bytes = await response.read()
                if response.status != 200:
                    error_text = self._format_error(response_bytes)
                    raise RuntimeError(
                        f"GPT-SoVITS request failed: "
                        f"HTTP {response.status}: {error_text}"
                    )

                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    error_text = self._format_error(response_bytes)
                    raise RuntimeError(
                        f"GPT-SoVITS returned JSON instead of WAV: {error_text}"
                    )

                return response_bytes

    @staticmethod
    def _format_error(response_bytes: bytes, max_len: int = 500) -> str:
        """Format GPT-SoVITS error responses for log-friendly output."""

        text = response_bytes.decode("utf-8", errors="replace")
        try:
            body = json.loads(text)
        except json.JSONDecodeError:
            return text[:max_len]

        if isinstance(body, dict):
            message = str(body.get("message", "")).strip()
            detail = str(body.get("Exception", "")).strip()
            if detail:
                first_line = detail.splitlines()[0].strip()
                merged = f"{message}: {first_line}" if message else first_line
                return merged[:max_len]
            if message:
                return message[:max_len]

        return text[:max_len]
