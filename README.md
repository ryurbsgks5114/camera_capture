# 📷 Camera Capture - Raspberry Pi Server

라즈베리파이 환경에서 카메라(사이드, 탑)를 제어하고, Flask 웹 서버를 통해 원격(프론트 GUI 애플리케이션)으로부터 명령을 받아 백그라운드에서 촬영 및 저장 업무를 수행하는 메인 백엔드 시스템입니다.

---

## 📂 폴더 구조 (Directory Structure)

```text
camera_capture/
│
├─ server.py                     # Flask 서버 실행 및 라우트 등록
├─ config.py                     # 카메라, 촬영 간격, 저장 경로 등 일반 설정
├─ secret_config.py              # FTP 주소, 포트, 계정 및 비밀번호 등 민감정보
├─ main.py                       # 서버 없이 라즈베리파이에서 단독으로 카메라 촬영 루프를 실행하는 독립형 진입점
│
├─ camera/                       # 카메라 촬영 및 로컬 저장 폴더
│   ├─ capture.py                # 카메라 촬영
│   └─ storage.py                # 사진 로컬 저장 폴더 생성 및 경로 반환 
│
├─ services/                     # 주요 기능 및 서비스 로직
│   ├─ capture_service.py        # 카메라 촬영, 자동 촬영 및 라즈베리파이 단독 실행용 기능 
│   └─ ftp_service.py            # FTP 폴더 생성 및 사진 업로드
│
└─ api/                          # GUI에서 호출하는 HTTP API
    ├─ status.py                 # 서버 및 촬영 상태 조회 (/status)
    ├─ capture.py                # 촬영 시작·중지 요청 처리 (/start, /stop)
    └─ routes.py                 # API 경로 등록
```

## 🔌 API 명세서 (API Documentation)

### 1. 시스템 상태 조회 (`GET /status`)
현재 서버의 구동 상태 및 촬영 진행 여부를 확인합니다.

* **Method:** `GET`
* **Endpoint:** `/status`
* **Request Body:** 없음 (`None`)
* **Response (Success - 200 OK):**
  * **촬영 중이 아닐 때 (`stopped`):**
    ```json
    {
      "server": "running",
      "capture": "stopped"
    }
    ```
  * **촬영 중일 때 (`running`):**
    ```json
    {
      "server": "running",
      "capture": "running",
      "interval_minutes": 1
    }
    ```

---

### 2. 카메라 촬영 시작 (`POST /start`)
지정된 시작 시간과 촬영 간격, 저장 방식에 따라 백그라운드 스레드에서 주기적인 카메라 촬영을 시작합니다.

* **Method:** `POST`
* **Endpoint:** `/start`
* **Request Body (JSON):**
  ```json
  {
    "start_time": "09:00:00",       // (필수) 촬영 시작 시간 (HH:MM:SS 형식)
    "interval_minutes": 1,          // (선택) 촬영 간격 (분 단위, 생략 시 config.py의 기본값 적용)
    "storage_mode": "both",         // (선택) 저장 방식 ("local" | "ftp" | "both", 기본값: "both")
    "ftp": {                        // storage_mode가 "ftp" 또는 "both"일 때 필수
      "host": "127.0.0.1",          // (필수) FTP 서버 주소
      "port": 5000,                 // (필수) FTP 포트 번호 (숫자)
      "user": "username",           // (필수) FTP 계정 아이디
      "password": "password",       // (필수) FTP 비밀번호
      "base_dir": "/remote/path"    // (필수) 원격 저장 기본 디렉토리 경로
    }
  }
  ```
* **Response (Success - 200 OK):**
  ```json
  {
    "success": true,
    "message": "촬영을 시작했습니다.",
    "start_time": "09:00:00",
    "interval_minutes": 1,
    "storage_mode": "both"
  }
  ```

---

### 3. 카메라 촬영 중지 (`POST /stop`)
현재 실행 중인 백그라운드 촬영 루프를 중지합니다.

* **Method:** `POST`
* **Endpoint:** `/stop`
* **Request Body:** 없음 (`None`)
* **Response (Success - 200 OK):**
  ```json
  {
    "success": true,
    "message": "촬영 중지 명령을 전달했습니다."
  }