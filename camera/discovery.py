import re
import subprocess
from config import (BY_PATH_DIR, SIDE_USB_PATH_KEY, TOP_USB_PATH_KEY,)

# ==========================================
# 비디오 장치 영상 포맷 지원 여부 확인 함수
# ==========================================
def is_capture_capable(device_path):
    try:
        # V4L2 유틸리티를 사용하여 지정된 비디오 장치의 지원 포맷 목록 조회
        result = subprocess.run(
            ["v4l2-ctl", "-d", str(device_path), "--list-formats-ext"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=5
        )

        # 명령어 실행 실패 시 촬영 불가 장치로 판단
        if result.returncode != 0:
            return False

        # 출력된 결과 중 [숫자]: ' 또는 [숫자]: " 형태의 패턴이 존재하는지 확인
        return bool(re.search(r"\[\d+\]:\s*['\"]", result.stdout))
    except (OSError, subprocess.TimeoutExpired):
        return False

# ==========================================
# USB 물리 경로 기반 촬영 가능 장치 검색 함수
# ==========================================
def find_camera_for_usb_path(path_key):
    # 시스템에 v4l/by-path 디렉터리가 존재하는지 확인
    if not BY_PATH_DIR.is_dir():
        print("[카메라 인식] by-path 디렉터리가 없습니다.")
        return None

    # by-path 안에서 video-index가 포함된 모든 후보 탐색 및 정렬
    candidates = sorted(BY_PATH_DIR.glob("*video-index*"))

    # 전달받은 USB 포트 경로 키워드에 속하는 장치 노드만 필터링
    candidates = [
        path for path in candidates
        if path_key in path.name
    ]

    # 우선순위 정렬: index0을 먼저 검사하고, 촬영 불가하면 그 외 인덱스 번호 순으로 검사
    candidates.sort(
        key=lambda path: (
            "video-index0" not in path.name,
            path.name
        )
    )

    # 필터링 및 정렬된 후보 장치들을 순회하며 촬영 가능 여부 검사
    for candidate in candidates:
        # 파일이 실제로 존재하는지 확인
        if not candidate.exists():
            continue

        # 실제 캡처 호환성이 확인된 장치일 경우 해당 경로 문자열 반환
        if is_capture_capable(candidate):
            print("[카메라 인식] 장치 발견:", path_key, "->", candidate)
            return str(candidate)

    print("[카메라 인식] 촬영 가능한 장치를 찾지 못했습니다:", path_key)

    return None

# ==========================================
# 측면 및 탑 카메라 전체 탐색 함수
# ==========================================
def discover_cameras():
    side_camera = find_camera_for_usb_path(SIDE_USB_PATH_KEY)
    top_camera = find_camera_for_usb_path(TOP_USB_PATH_KEY)

    return {
        "side": side_camera,
        "top": top_camera
    }