"""Command line entry point for the bridge."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
from functools import partial

from wyoming.info import Attribution, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncServer

from . import __version__
from .config import SovitsConfig
from .handler import SovitsEventHandler
from .sovits_client import SovitsClient

_LOGGER = logging.getLogger(__name__)


def env(name: str, default: str) -> str:
    """Return an environment variable with a default."""

    return os.environ.get(name, default)


def env_bool(name: str, default: bool) -> bool:
    """Parse a boolean environment variable."""

    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def comma_list(value: str) -> list[str]:
    """Parse a comma-separated list."""

    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uri",
        default=env("WYOMING_URI", "tcp://0.0.0.0:10200"),
        help="Wyoming server URI, e.g. tcp://0.0.0.0:10200",
    )
    parser.add_argument(
        "--sovits-url",
        default=env("SOVITS_URL", "http://127.0.0.1:9880/tts"),
        help="GPT-SoVITS /tts URL",
    )
    parser.add_argument(
        "--ref-audio-path",
        default=os.environ.get("SOVITS_REF_AUDIO_PATH"),
        required=os.environ.get("SOVITS_REF_AUDIO_PATH") is None,
        help="Reference audio path visible to the GPT-SoVITS server",
    )
    parser.add_argument(
        "--aux-ref-audio-paths",
        default=env("SOVITS_AUX_REF_AUDIO_PATHS", ""),
        help="Comma-separated auxiliary reference audio paths",
    )
    parser.add_argument(
        "--prompt-text",
        default=env("SOVITS_PROMPT_TEXT", ""),
        help="Transcript of the reference audio",
    )
    parser.add_argument(
        "--prompt-lang",
        default=env("SOVITS_PROMPT_LANG", "ko"),
        help="Language of the reference audio prompt",
    )
    parser.add_argument(
        "--text-lang",
        default=env("SOVITS_TEXT_LANG", "ko"),
        help="Language of text to synthesize",
    )
    parser.add_argument("--top-k", type=int, default=int(env("SOVITS_TOP_K", "15")))
    parser.add_argument("--top-p", type=float, default=float(env("SOVITS_TOP_P", "1")))
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(env("SOVITS_TEMPERATURE", "1")),
    )
    parser.add_argument(
        "--text-split-method",
        default=env("SOVITS_TEXT_SPLIT_METHOD", "cut5"),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(env("SOVITS_BATCH_SIZE", "1")),
    )
    parser.add_argument(
        "--batch-threshold",
        type=float,
        default=float(env("SOVITS_BATCH_THRESHOLD", "0.75")),
    )
    parser.add_argument(
        "--split-bucket",
        action=argparse.BooleanOptionalAction,
        default=env_bool("SOVITS_SPLIT_BUCKET", True),
    )
    parser.add_argument(
        "--speed-factor",
        type=float,
        default=float(env("SOVITS_SPEED_FACTOR", "1.0")),
    )
    parser.add_argument(
        "--fragment-interval",
        type=float,
        default=float(env("SOVITS_FRAGMENT_INTERVAL", "0.3")),
    )
    parser.add_argument("--seed", type=int, default=int(env("SOVITS_SEED", "-1")))
    parser.add_argument(
        "--parallel-infer",
        action=argparse.BooleanOptionalAction,
        default=env_bool("SOVITS_PARALLEL_INFER", True),
    )
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        default=float(env("SOVITS_REPETITION_PENALTY", "1.35")),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(env("SOVITS_TIMEOUT_SECONDS", "120")),
    )
    parser.add_argument(
        "--samples-per-chunk",
        type=int,
        default=int(env("SAMPLES_PER_CHUNK", "1024")),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=env_bool("DEBUG", False),
        help="Enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )
    return parser


async def main() -> None:
    """Run the Wyoming server."""

    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    sovits_config = SovitsConfig(
        url=args.sovits_url,
        ref_audio_path=args.ref_audio_path,
        prompt_text=args.prompt_text,
        prompt_lang=args.prompt_lang,
        text_lang=args.text_lang,
        aux_ref_audio_paths=comma_list(args.aux_ref_audio_paths),
        top_k=args.top_k,
        top_p=args.top_p,
        temperature=args.temperature,
        text_split_method=args.text_split_method,
        batch_size=args.batch_size,
        batch_threshold=args.batch_threshold,
        split_bucket=args.split_bucket,
        speed_factor=args.speed_factor,
        fragment_interval=args.fragment_interval,
        seed=args.seed,
        parallel_infer=args.parallel_infer,
        repetition_penalty=args.repetition_penalty,
        timeout_seconds=args.timeout_seconds,
    )

    voice = TtsVoice(
        name="gpt-sovits",
        description="GPT-SoVITS configured voice",
        attribution=Attribution(
            name="GPT-SoVITS",
            url="https://github.com/RVC-Boss/GPT-SoVITS",
        ),
        installed=True,
        languages=[args.text_lang],
        version=None,
    )
    wyoming_info = Info(
        tts=[
            TtsProgram(
                name="gpt-sovits",
                description="GPT-SoVITS text to speech bridge",
                attribution=Attribution(
                    name="GPT-SoVITS",
                    url="https://github.com/RVC-Boss/GPT-SoVITS",
                ),
                installed=True,
                voices=[voice],
                version=__version__,
                supports_synthesize_streaming=True,
            )
        ],
    )

    sovits_client = SovitsClient(sovits_config)
    server = AsyncServer.from_uri(args.uri)

    _LOGGER.info("Starting Wyoming server on %s", args.uri)
    _LOGGER.info("Using GPT-SoVITS endpoint %s", args.sovits_url)

    server_task = asyncio.create_task(
        server.run(partial(SovitsEventHandler, wyoming_info, args, sovits_client))
    )
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, server_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, server_task.cancel)

    try:
        await server_task
    except asyncio.CancelledError:
        _LOGGER.info("Server stopped")


def run() -> None:
    """Entrypoint used by packaging."""

    asyncio.run(main())


if __name__ == "__main__":
    run()
