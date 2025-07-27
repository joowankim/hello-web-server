# Hello Web Server

## 프로젝트 소개

**Hello Web Server**는 WSGI 호환 웹 서버를 처음부터 구현하는 학습 프로젝트입니다. Gunicorn과 같은 프로덕션 웹 서버의 동작 원리를 이해하고, HTTP 프로토콜 파싱부터 요청-응답 처리까지 웹 서버의 핵심 기능들을 직접 구현해보는 것을 목표로 합니다.

## 주요 특징

- **WSGI 호환**: Python 웹 애플리케이션을 위한 표준 인터페이스 구현
- **HTTP 프로토콜 지원**: HTTP/1.0, HTTP/1.1 요청 파싱 및 응답 처리
- **청크 전송 인코딩**: Transfer-Encoding: chunked 지원
- **요청 본문 처리**: Content-Length 및 청크 방식 요청 본문 파싱
- **연결 관리**: keep-alive 및 close 연결 처리
- **에러 핸들링**: 400, 500 등 HTTP 에러 상태 코드 처리

## 기술 스택

- **Python 3.13+**: 최신 Python 기능 활용
- **Socket Programming**: TCP 소켓을 이용한 저수준 네트워크 프로그래밍
- **Type Hints**: 타입 안전성을 위한 완전한 타입 어노테이션
- **pytest**: 포괄적인 테스트 커버리지

## 프로젝트 구조

```
hello-web-server/
├── main.py              # 서버 실행 진입점
├── web_server/          # 웹 서버 핵심 모듈
│   ├── worker.py        # 메인 워커 프로세스
│   ├── connection.py    # 클라이언트 연결 관리
│   ├── cycle.py         # 요청-응답 사이클 처리
│   ├── wsgi.py          # WSGI 인터페이스 구현
│   ├── config.py        # 서버 설정 관리
│   └── http/            # HTTP 프로토콜 구현
│       ├── parser.py    # HTTP 요청 파서
│       ├── message.py   # 요청/응답 메시지 처리
│       ├── body.py      # 요청 본문 처리
│       └── reader.py    # 소켓 데이터 읽기
└── tests/               # 단위 테스트 및 통합 테스트
```

## 학습 목표

이 프로젝트는 다음과 같은 웹 서버 개념들을 실제 구현을 통해 학습할 수 있도록 설계되었습니다:

1. **HTTP 프로토콜 이해**: 요청 라인, 헤더, 본문 파싱
2. **소켓 프로그래밍**: TCP 소켓을 이용한 클라이언트-서버 통신
3. **WSGI 인터페이스**: Python 웹 애플리케이션과 웹 서버 간 표준 인터페이스
4. **에러 처리**: HTTP 에러 상태 코드 및 예외 처리

## 시작하기

### 요구사항

- Python 3.13+
- uv (패키지 매니저)

### 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/your-username/hello-web-server.git
cd hello-web-server

# 의존성 설치
uv sync

# 서버 실행
uv run python main.py
```

서버가 실행되면 `http://localhost:8000`에서 "Hello, World!" 메시지를 확인할 수 있습니다.

### 테스트 실행

```bash
# 모든 테스트 실행
uv run pytest

# 특정 테스트 실행
uv run pytest .

# 커버리지 포함 테스트
uv run pytest --cov=web_server
```

## 영감

이 프로젝트는 ["Build Your Own X" 프로젝트](https://github.com/codecrafters-io/build-your-own-x)에서 영감을 받아 시작되었으며, Gunicorn의 테스트 케이스를 참고하여 실제 프로덕션 웹 서버와 유사한 동작을 구현하는 것을 목표로 합니다.

---

_이 프로젝트는 학습 목적으로 제작되었으며, 프로덕션 환경에서의 사용은 권장하지 않습니다._
