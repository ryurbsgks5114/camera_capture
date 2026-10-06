from pathlib import Path
from secret_config import (
    FTP_HOST as SECRET_FTP_HOST,
    FTP_PORT as SECRET_FTP_PORT,
    FTP_USER as SECRET_FTP_USER,
    FTP_PASSWORD as SECRET_FTP_PASSWORD
)

# ==========================================
# 1. 카메라 설정
# ==========================================

# 사이드 카메라
SIDE_CAMERA = "/dev/video0"

# 탑 카메라
TOP_CAMERA = "/dev/video2"

# ==========================================
# 2. 촬영 설정
# ==========================================

# 촬영 간격 (분)
INTERVAL_MINUTES = 1

# ==========================================
# 3. 로컬 저장 설정
# ==========================================

# 사진 저장 폴더
OUTPUT_DIR = Path.home() / "camera_capture" / "photos"

# ==========================================
# 4. FTP 설정
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