"""Runtime configuration for the bridge."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SovitsConfig:
    """Configuration for GPT-SoVITS synthesis requests."""

    url: str
    ref_audio_path: str
    prompt_text: str
    prompt_lang: str
    text_lang: str
    aux_ref_audio_paths: list[str]
    top_k: int
    top_p: float
    temperature: float
    text_split_method: str
    batch_size: int
    batch_threshold: float
    split_bucket: bool
    speed_factor: float
    fragment_interval: float
    seed: int
    parallel_infer: bool
    repetition_penalty: float
    timeout_seconds: float

    def build_payload(self, text: str) -> dict[str, object]:
        """Build a GPT-SoVITS `/tts` request payload."""

        return {
            "text": text,
            "text_lang": self.text_lang,
            "ref_audio_path": self.ref_audio_path,
            "aux_ref_audio_paths": self.aux_ref_audio_paths,
            "prompt_text": self.prompt_text,
            "prompt_lang": self.prompt_lang,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "text_split_method": self.text_split_method,
            "batch_size": self.batch_size,
            "batch_threshold": self.batch_threshold,
            "split_bucket": self.split_bucket,
            "speed_factor": self.speed_factor,
            "fragment_interval": self.fragment_interval,
            "seed": self.seed,
            "parallel_infer": self.parallel_infer,
            "repetition_penalty": self.repetition_penalty,
            "media_type": "wav",
            "streaming_mode": False,
        }
