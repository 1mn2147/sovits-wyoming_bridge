# GPT-SoVITS Wyoming Bridge TODO

## 1. GPT-SoVITS API 준비
- [x] GPT-SoVITS를 WebUI가 아닌 API 모드로 실행한다.
- [x] `/tts` 엔드포인트가 `POST` JSON 요청을 받고 WAV 바이트를 반환하는지 확인한다.
- [x] 브릿지 컨테이너에서 접근 가능한 API URL을 정한다. 예: `http://gpt-sovits:9880/tts`
- [x] GPT-SoVITS 서버 기준 `ref_audio_path` 경로를 확정한다.
- [x] `text_lang`, `prompt_lang`, `prompt_text` 기본값을 확정한다.

진행 메모 (2026-05-05):
- `api_v2.py`는 컨테이너에서 기동 확인.
- 현재 확인된 URL: `http://127.0.0.1:9880/tts` (호스트 기준), docker 내부에서는 `host.docker.internal:9880`.
- 기본 검증값: `ref_audio_path=/tmp/ref.wav`, `text_lang=zh`, `prompt_lang=zh`, `prompt_text=测试`
- `nvidia-npp-cu12` 설치 + `LD_LIBRARY_PATH=/root/conda/lib:$LD_LIBRARY_PATH`로 `Could not load libtorchcodec` 해결.

## 2. Wyoming Bridge 서버
- [x] Python 패키지 골격을 만든다.
- [x] Wyoming `Describe` 이벤트에 TTS capability 정보를 반환한다.
- [x] Wyoming `Synthesize` 이벤트에서 텍스트를 추출한다.
- [x] Wyoming streaming 입력 이벤트(`SynthesizeStart`, `SynthesizeChunk`, `SynthesizeStop`)를 수신한다.
- [x] GPT-SoVITS `/tts`에 합성 요청을 보낸다.
- [x] 반환된 WAV를 PCM `AudioStart`/`AudioChunk`/`AudioStop` 이벤트로 변환한다.
- [x] GPT-SoVITS 오류를 Wyoming `Error` 이벤트로 반환한다.
- [x] CLI 인자와 환경 변수로 포트/API/참조 음성/언어/샘플링 옵션을 설정한다.

## 3. Docker 배포
- [x] Dockerfile을 작성한다.
- [x] docker-compose 예시를 작성한다.
- [x] `.dockerignore`를 작성한다.
- [x] 컨테이너 기본 포트를 Wyoming 기본 관례인 `10200`으로 노출한다.

## 4. Home Assistant 연동
- [x] README에 Wyoming 통합 등록 절차를 문서화한다.
- [ ] Home Assistant에서 `설정 -> 기기 및 서비스 -> Wyoming`으로 브릿지를 등록한다.
- [ ] 음성 파이프라인에서 TTS 엔진으로 노출되는지 확인한다.
- [ ] 실제 문장 합성 테스트를 수행한다.

## 5. 검증
- [x] WAV chunk 변환 단위 테스트를 추가한다.
- [x] GPT-SoVITS payload 생성 단위 테스트를 추가한다.
- [x] Wyoming TTS smoke test 스크립트를 추가한다.
- [x] 실제 GPT-SoVITS 서버와 통합 테스트를 수행한다.
- [ ] Home Assistant Wyoming 클라이언트와 end-to-end 테스트를 수행한다.

진행 메모 (2026-05-05):
- `/tts` 직접 호출: `HTTP 200`, `content-type: audio/wav`, `154924 bytes` 확인.
- `scripts/smoke_wyoming_tts.py`로 브릿지 <-> SoVITS 실호출 성공: `AUDIO_START rate=32000, OK chunks=54`.
