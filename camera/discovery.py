import re
import subprocess
import pythoncom
from comgrab3 import enumerate_cameras
from config import (SIDE_CAMERA_LOCATION_ID, TOP_CAMERA_LOCATION_ID)

# 서버 실행 중 사용할 카메라 매칭 결과
_cached_cameras = None
# 카메라 검색 중 발생한 오류 메시지
_camera_mapping_error = None

# ==========================================
# USB 물리 경로 기반 카메라 검색 함수
# ==========================================
def find_camera_for_usb_path(path_key, cameras):
    # USB 물리 경로가 설정되지 않은 경우 검색 종료
    if not path_key:
        return None

    # 전달받은 USB 물리 경로와 일치하는 카메라 검색
    for camera in cameras:
        camera_location_id = camera.get("location_id", "")

        if camera_location_id.lower() == path_key.lower():
            return camera

    print("[카메라 인식 실패] USB 물리 경로:", path_key)

    return None

# ==========================================
# FFmpeg DirectShow 장치 목록 조회 함수
# ==========================================
def enumerate_ffmpeg_cameras():
    command = ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]

    try:
        # FFmpeg 장치 목록 조회(dummy 입력 파일이 없으므로 종료 코드가 0이 아닐 수 있음)
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            errors="replace",
            timeout=15,
            check=False
        )

        output = (result.stdout or "") + "\n" + (result.stderr or "")

        # Alternative name에서 DirectShow 장치 경로 추출
        alternative_names = re.findall(r'Alternative name "([^"]+)"', output)

        # PnP 장치만 추출
        ffmpeg_devices = []

        for alternative_name in alternative_names:
            if alternative_name.lower().startswith("@device_pnp_"):
                ffmpeg_devices.append(alternative_name)

        print("---------- FFmpeg DirectShow 카메라 목록 ----------")

        for device_name in ffmpeg_devices:
            print("FFmpeg 장치:", device_name)

        print("----------------------------------------")

        return ffmpeg_devices
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg 카메라 목록 조회 시간이 초과되었습니다.")
    except OSError as error:
        raise RuntimeError("FFmpeg 카메라 목록 조회에 실패했습니다: " + str(error))

# ==========================================
# 장치 경로 정규화 함수
# ==========================================
def normalize_device_path(device_path):
    if not device_path:
        return ""

    normalized_path = device_path.strip()

    # FFmpeg Alternative name에 붙는 접두어 제거
    prefix = "@device_pnp_"

    if normalized_path.lower().startswith(prefix):
        normalized_path = normalized_path[len(prefix):]

    # 대소문자 차이를 무시하고 비교
    return normalized_path.casefold()

# ==========================================
# comgrab3 카메라와 FFmpeg 장치 매칭 함수
# ==========================================
def match_ffmpeg_device(camera, ffmpeg_devices):
    if not camera:
        return None

    # comgrab3에서 제공한 Windows 장치 경로
    camera_device_path = camera.get("device_path", "")

    if not camera_device_path:
        print("[FFmpeg 매칭 실패] comgrab3 device_path가 없습니다.")
        
        return None

    # 비교를 위해 장치 경로 정규화
    target_path = normalize_device_path(camera_device_path)

    # FFmpeg 장치 목록에서 동일한 경로 검색
    matched_devices = []

    for ffmpeg_device in ffmpeg_devices:
        ffmpeg_path = normalize_device_path(ffmpeg_device)

        if ffmpeg_path == target_path:
            matched_devices.append(ffmpeg_device)

    # 일치하는 장치가 정확히 하나가 아닌 경우 실패 처리
    if len(matched_devices) != 1:
        print(
            "[FFmpeg 매칭 실패] 일치하는 장치 수:",
            len(matched_devices),
            "카메라:",
            camera.get("name"),
            "USB 경로:",
            camera.get("location_id")
        )

        return None

    matched_device = matched_devices[0]

    # 기존 카메라 정보는 유지하고 FFmpeg 장치명 추가
    matched_camera = dict(camera)
    matched_camera["dshow_device_name"] = matched_device

    print("[FFmpeg 자동 매칭 완료]", camera.get("location_id"), "->", matched_device)

    return matched_camera

# ==========================================
# 사이드 및 탑 카메라 전체 탐색 함수
# ==========================================
def discover_cameras():
    try:
        # Windows COM 초기화
        pythoncom.CoInitialize()

        # 연결된 USB 카메라 목록 조회
        cameras = enumerate_cameras()

        print("---------- comgrab3 카메라 목록 ----------")

        for camera in cameras:
            print("카메라 이름:", camera.get("name"))
            print("USB 물리 경로:", camera.get("location_id"))
            print("----------------------------------------")

        # USB 물리 경로를 기준으로 측면 및 상단 카메라 검색
        side_camera = find_camera_for_usb_path(SIDE_CAMERA_LOCATION_ID, cameras)
        top_camera = find_camera_for_usb_path(TOP_CAMERA_LOCATION_ID, cameras)

        # FFmpeg DirectShow 장치 목록 조회
        ffmpeg_devices = enumerate_ffmpeg_cameras()

        # USB 카메라와 FFmpeg 장치명 자동 매칭
        side_camera = match_ffmpeg_device(side_camera,ffmpeg_devices)
        top_camera = match_ffmpeg_device(top_camera, ffmpeg_devices)

        return {
            "side": side_camera,
            "top": top_camera
        }
    finally:
        # Windows COM 초기화 해제
        pythoncom.CoUninitialize()

# ==========================================
# 서버 시작 시 카메라 자동 매칭 및 결과 저장
# ==========================================
def initialize_camera_mapping():
    global _cached_cameras
    global _camera_mapping_error

    print("========================================")
    print("카메라 자동 매칭 시작")

    try:
        # USB 물리 경로와 FFmpeg 장치명 자동 매칭
        detected_cameras = discover_cameras()

        # 검색 결과를 메모리에 보관
        _cached_cameras = detected_cameras
        _camera_mapping_error = None

        return True
    except Exception as error:
        # 검색 실패 시 빈 결과를 보관하고 오류 내용 저장
        _cached_cameras = {
            "side": None,
            "top": None
        }
        _camera_mapping_error = str(error)

        print("[카메라 자동 매칭 오류]", error)
        print("========================================")

        return False

# ==========================================
# 메모리에 저장된 카메라 매칭 결과 가져오기
# ==========================================
def get_cached_cameras():
    return _cached_cameras

# ==========================================
# 카메라 매칭 결과 및 오류 정보 초기화
# ==========================================
def clear_camera_mapping():
    global _cached_cameras
    global _camera_mapping_error

    _cached_cameras = None
    _camera_mapping_error = None

    print("[카메라 자동 매칭] 메모리 정보 초기화 완료")

# ==========================================
# 카메라 매칭 오류 메시지 가져오기
# ==========================================
def get_camera_mapping_error():
    return _camera_mapping_error