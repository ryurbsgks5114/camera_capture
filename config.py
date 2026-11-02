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

# 측면 카메라와 상단 카메라의 USB 물리적 경로
SIDE_CAMERA_LOCATION_ID = (
    "PCIROOT(0)#PCI(1400)#USBROOT(0)#USB(9)#USBMI(0)"
)
TOP_CAMERA_LOCATION_ID = (
    "PCIROOT(0)#PCI(1400)#USBROOT(0)#USB(1)#USBMI(0)"
)

# FFmpeg DirectShow 카메라 고유 장치명
SIDE_CAMERA_DSHOW_NAME = (
    r"@device_pnp_\\?\usb#vid_2757&pid_1303&mi_00#6&39f69e8c&0&0000"
    r"#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global"
)
TOP_CAMERA_DSHOW_NAME = (
    r"@device_pnp_\\?\usb#vid_2757&pid_1303&mi_00#6&35f8257f&0&0000"
    r"#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global"
)

# 현재 테스트는 측면 카메라 1대만 사용
# 두 카메라 테스트로 돌아갈 때 True로 변경
ENABLE_TOP_CAMERA = True

# 카메라 촬영 해상도
CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080

# ==========================================
# 촬영 설정
# ==========================================

# 촬영 간격 (분)
INTERVAL_MINUTES = 1

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