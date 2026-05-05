# GPT-SoVITS Wyoming Connector

Home Assistant의 Wyoming TTS 파이프라인과 GPT-SoVITS API 서버를 연결하는 브릿지입니다.

```text
Home Assistant Wyoming Integration
  <-> TCP Wyoming Protocol
    <-> sovits-wyoming-connector
      <-> HTTP POST /tts
        <-> GPT-SoVITS API Server
```

## GPT-SoVITS API 실행

GPT-SoVITS 서버에서 API 모드를 실행하고 `/tts` 엔드포인트가 열려 있어야 합니다.

```bash
LD_LIBRARY_PATH=/root/conda/lib:$LD_LIBRARY_PATH \
python api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

GPT-SoVITS의 `/tts` 요청에는 최소한 `text`, `text_lang`, `ref_audio_path`, `prompt_lang`이 필요합니다. `ref_audio_path`는 브릿지 컨테이너가 아니라 GPT-SoVITS 서버 프로세스가 접근할 수 있는 경로여야 합니다.

## 로컬 실행

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/sovits-wyoming-connector \
  --uri tcp://0.0.0.0:10200 \
  --sovits-url http://127.0.0.1:9880/tts \
  --ref-audio-path /data/ref.wav \
  --prompt-lang ko \
  --text-lang ko \
  --prompt-text "참조 오디오의 발화 문장"
```

별도 터미널에서 Wyoming 스모크 테스트:

```bash
.venv/bin/python scripts/smoke_wyoming_tts.py \
  --uri tcp://127.0.0.1:10200 \
  --text "브릿지 테스트 문장입니다"
```

## Docker Compose

```bash
docker compose up --build
```

환경 변수는 `docker-compose.yml`에서 조정합니다.

## Home Assistant 등록

1. Home Assistant에서 `설정 -> 기기 및 서비스 -> 통합 구성요소 추가`를 엽니다.
2. `Wyoming`을 검색해 추가합니다.
3. 브릿지 서버의 IP와 포트 `10200`을 입력합니다.
4. 음성 비서 파이프라인의 TTS 엔진으로 `GPT-SoVITS`를 선택합니다.

## 주요 설정

| 옵션 | 환경 변수 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `--uri` | `WYOMING_URI` | `tcp://0.0.0.0:10200` | Wyoming 서버 URI |
| `--sovits-url` | `SOVITS_URL` | `http://127.0.0.1:9880/tts` | GPT-SoVITS `/tts` URL |
| `--ref-audio-path` | `SOVITS_REF_AUDIO_PATH` | 필수 | GPT-SoVITS 서버에서 접근 가능한 참조 음성 |
| `--prompt-text` | `SOVITS_PROMPT_TEXT` | 빈 문자열 | 참조 음성의 원문 |
| `--prompt-lang` | `SOVITS_PROMPT_LANG` | `ko` | 참조 음성 언어 |
| `--text-lang` | `SOVITS_TEXT_LANG` | `ko` | 합성할 텍스트 언어 |
| `--samples-per-chunk` | `SAMPLES_PER_CHUNK` | `1024` | Wyoming PCM chunk 크기 |

## 현재 범위

이 브릿지는 GPT-SoVITS에서 WAV를 받아 Wyoming PCM 스트림으로 변환합니다. Wyoming 텍스트 streaming 입력은 지원하지만, GPT-SoVITS 요청은 `SynthesizeStop` 시점에 한 번 수행합니다.

## 트러블슈팅

- `/tts`가 `HTTP 400`과 함께 `Could not load libtorchcodec`를 반환하는 경우:
  컨테이너에서 아래를 먼저 적용합니다.

```bash
python -m pip install nvidia-npp-cu12==12.2.5.30
LD_LIBRARY_PATH=/root/conda/lib:$LD_LIBRARY_PATH \
python api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

이후 `/tts`가 `HTTP 200`으로 WAV를 반환해야 합니다. 실패 시 브릿지는 Wyoming `error` 이벤트를 반환합니다.
- `ref_audio_path`는 브릿지 경로가 아니라 GPT-SoVITS 프로세스 기준 파일 경로여야 합니다.

## Acknowledgments

This project is a bridge connecting the following open-source projects:

- GPT-SoVITS (MIT License): https://github.com/RVC-Boss/GPT-SoVITS
- Wyoming protocol (MIT License): https://github.com/OHF-Voice/wyoming

Special thanks to the original authors and maintainers.

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE).
