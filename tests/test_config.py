from sovits_wyoming_connector.config import SovitsConfig


def test_build_payload_contains_gpt_sovits_required_fields() -> None:
    config = SovitsConfig(
        url="http://127.0.0.1:9880/tts",
        ref_audio_path="/data/ref.wav",
        prompt_text="prompt",
        prompt_lang="ko",
        text_lang="ko",
        aux_ref_audio_paths=[],
        top_k=15,
        top_p=1,
        temperature=1,
        text_split_method="cut5",
        batch_size=1,
        batch_threshold=0.75,
        split_bucket=True,
        speed_factor=1.0,
        fragment_interval=0.3,
        seed=-1,
        parallel_infer=True,
        repetition_penalty=1.35,
        timeout_seconds=120,
    )

    payload = config.build_payload("hello")

    assert payload["text"] == "hello"
    assert payload["text_lang"] == "ko"
    assert payload["ref_audio_path"] == "/data/ref.wav"
    assert payload["prompt_lang"] == "ko"
    assert payload["media_type"] == "wav"
    assert payload["streaming_mode"] is False
