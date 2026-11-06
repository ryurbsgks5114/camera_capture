from pathlib import Path
from secret_config import (
    FTP_HOST as SECRET_FTP_HOST,
    FTP_PORT as SECRET_FTP_PORT,
    FTP_USER as SECRET_FTP_USER,
    FTP_PASSWORD as SECRET_FTP_PASSWORD
)

# ==========================================
# 카메라 설정
# ==========================================

# Side / Top 카메라 역할은 최초 설정 시 GUI에서 지정하고
# camera_config.json 파일에 저장하여 관리
ENABLE_TOP_CAMERA = True

# 카메라 촬영 해상도
CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080

CAMERA_PREOPEN_SECONDS = 5

FRAME_MAX_AGE_MS = 500

CAMERA_SYNC_TOLERANCE_MS = 500

# ==========================================
# 촬영 설정
# ==========================================

# 촬영 간격 (분)
INTERVAL_MINUTES = 10

# ==========================================
# 로컬 저장 설정
# ==========================================

# 사진 저장 폴더
OUTPUT_DIR = Path(__file__).resolve().parent / "photos"

# ==========================================
# FTP 설정
# ==========================================

# FTP 서버 주소
FTP_HOST = SECRET_FTP_HOST

# FTP 서버 포트
FTP_PORT = SECRET_FTP_PORT

# FTP 로그인 아이디
FTP_USER = SECRET_FTP_USER

# FTP 로그인 비밀번호
FTP_PASSWORD = SECRET_FTP_PASSWORD

# FTP 사진 저장 기본 폴더
FTP_BASE_DIR = "/test/camera"