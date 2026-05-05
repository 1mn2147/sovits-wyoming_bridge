Home Assistant의 Wyoming 파이프라인과 GPT-SoVITS API 사이를 연결해 주는 중간 브릿지(Bridge) 서버를 구성해야 합니다.

전체적인 동작 구조와 구현 방안은 다음과 같습니다.

1. 동작 구조 (Architecture)
Plaintext
Home Assistant 
  └── [Wyoming Integration] 
       <-- (Wyoming Protocol: TCP) --> 
         [Custom Wyoming Bridge] 
           <-- (HTTP/REST API) --> 
             [GPT-SoVITS API Server]
Wyoming 프로토콜은 매우 경량화된 오디오/텍스트 스트리밍 프로토콜입니다. 브릿지 서버는 HA로부터 텍스트 덩어리를 받아 GPT-SoVITS의 추론 엔드포인트로 넘기고, 생성된 오디오 파일(WAV 등)을 다시 PCM 스트림으로 변환하여 HA로 돌려주는 역할을 합니다.

2. 구현 단계
Step 1: GPT-SoVITS API 활성화
GPT-SoVITS를 WebUI 모드가 아닌 API 모드(일반적으로 FastAPI 기반)로 실행합니다. 특정 텍스트, 참조 오디오(Reference Audio), 화자 정보 등을 페이로드로 보내면 합성된 오디오를 반환하는 엔드포인트(예: http://<GPT-SoVITS-IP>:9880/)가 열려 있어야 합니다.

Step 2: Wyoming Bridge 애플리케이션 작성
Python의 공식 wyoming 라이브러리를 사용하여 브릿지 서버를 구축합니다. GitHub 등에 공개된 'Wyoming OpenAI TTS' 나 'Wyoming ElevenLabs' 브릿지 코드를 포크(Fork)하여 API 호출 부분만 GPT-SoVITS 규격에 맞게 수정하는 것이 가장 빠릅니다.

주요 로직: wyoming.tts.Synthesize 이벤트를 수신 -> GPT-SoVITS API에 POST 요청 -> 반환된 오디오 데이터를 wyoming.audio.AudioChunk로 변환하여 스트리밍.

Step 3: Docker 컨테이너화 및 배포
의존성 충돌을 막고 홈 서버 환경에 깔끔하게 통합하기 위해 작성한 브릿지 애플리케이션을 Docker Image로 빌드합니다. docker-compose.yml을 통해 10020과 같은 Wyoming 기본 포트를 열어 컨테이너를 실행합니다.

Step 4: Home Assistant 연동
Home Assistant의 설정 -> 기기 및 서비스 -> 통합 구성요소 추가에서 Wyoming을 검색하여 추가합니다. 브릿지 서버의 IP와 매핑한 포트를 입력하면 HA의 음성 비서 파이프라인에서 GPT-SoVITS를 TTS 엔진으로 선택할 수 있습니다.