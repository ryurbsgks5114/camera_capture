import re
import subprocess
import pythoncom
from comgrab3 import enumerate_cameras
from camera.configuration import load_camera_config, save_camera_config

# 서버 실행 중 사용할 카메라 매칭 결과
_cached_cameras = None
# 현재 PC에서 검색된 카메라 목록
_available_cameras = []
# 카메라 검색 중 발생한 오류 메시지
_camera_mapping_error = None

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

        output = (result.stdout or "") + "\\n" + (result.stderr or "")

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
# 현재 PC에 연결된 카메라 전체 검색 함수
# ==========================================
def discover_available_cameras():
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

        # FFmpeg DirectShow 장치 목록 조회
        ffmpeg_devices = enumerate_ffmpeg_cameras()

        # 모든 카메라에 FFmpeg 장치명 연결
        available_cameras = []

        for camera in cameras:
            matched_camera = match_ffmpeg_device(camera, ffmpeg_devices)

            camera_info = dict(camera)
            camera_info["dshow_device_name"] = (
                matched_camera.get("dshow_device_name")
                if matched_camera else None
            )

            available_cameras.append(camera_info)

        return available_cameras
    finally:
        # Windows COM 초기화 해제
        pythoncom.CoUninitialize()

# ==========================================
# 카메라 역할 설정에 맞춰 Side / Top 매칭
# ==========================================
def apply_camera_config(camera_config):
    global _cached_cameras
    global _camera_mapping_error

    side_camera_id = camera_config["side_camera_id"]
    top_camera_id = camera_config["top_camera_id"]

    side_camera = None
    top_camera = None

    for camera in _available_cameras:
        location_id = camera.get("location_id", "")

        if location_id.casefold() == side_camera_id.casefold():
            side_camera = camera

        if location_id.casefold() == top_camera_id.casefold():
            top_camera = camera

    if not side_camera or not top_camera:
        _cached_cameras = {"side": None, "top": None}
        _camera_mapping_error = (
            "저장된 카메라 설정과 현재 연결된 카메라가 일치하지 않습니다. "
            "카메라 역할을 다시 설정해 주세요."
        )
        print("[카메라 설정 확인 필요]", _camera_mapping_error)
        return False

    if not side_camera.get("dshow_device_name") or not top_camera.get("dshow_device_name"):
        _cached_cameras = {"side": None, "top": None}
        _camera_mapping_error = (
            "선택한 카메라의 FFmpeg 장치 연결에 실패했습니다. "
            "카메라 연결 상태를 확인해 주세요."
        )
        print("[카메라 설정 확인 필요]", _camera_mapping_error)
        return False

    _cached_cameras = {
        "side": side_camera,
        "top": top_camera
    }
    _camera_mapping_error = None

    print("[카메라 역할 매칭 완료] Side:", side_camera.get("location_id"))
    print("[카메라 역할 매칭 완료] Top:", top_camera.get("location_id"))

    return True

# ==========================================
# 서버 시작 시 카메라 자동 검색 및 설정 적용
# ==========================================
def initialize_camera_mapping():
    global _cached_cameras
    global _available_cameras
    global _camera_mapping_error

    print("========================================")
    print("카메라 자동 검색 시작")

    try:
        # 현재 PC에 연결된 카메라 전체 검색
        _available_cameras = discover_available_cameras()

        # 저장된 Side / Top 역할 설정 불러오기
        saved_config = load_camera_config()

        if not saved_config:
            _cached_cameras = {"side": None, "top": None}
            _camera_mapping_error = None

            print("[카메라 최초 설정 필요] GUI에서 Side / Top 카메라를 지정해 주세요.")
            print("========================================")

            return True

        # 저장된 역할 설정으로 카메라 자동 매칭
        return apply_camera_config(saved_config)
    except Exception as error:
        _available_cameras = []
        _cached_cameras = {"side": None, "top": None}
        _camera_mapping_error = str(error)

        print("[카메라 자동 검색 오류]", error)
        print("========================================")

        return False

# ==========================================
# 현재 검색된 카메라 목록 가져오기
# ==========================================
def get_available_cameras():
    return [
        {
            "name": camera.get("name", ""),
            "location_id": camera.get("location_id", ""),
            "dshow_device_name": camera.get("dshow_device_name")
        }
        for camera in _available_cameras
    ]

# ==========================================
# 저장된 카메라 역할 설정 가져오기
# ==========================================
def get_saved_camera_config():
    return load_camera_config()

# ==========================================
# GUI에서 지정한 카메라 역할 저장 및 적용
# ==========================================
def configure_cameras(side_camera_id, top_camera_id):
    global _cached_cameras
    global _camera_mapping_error

    if side_camera_id == top_camera_id:
        return False, "측면 카메라와 상단 카메라는 서로 달라야 합니다."

    camera_ids = {
        camera.get("location_id"): camera
        for camera in _available_cameras
    }

    side_camera = camera_ids.get(side_camera_id)
    top_camera = camera_ids.get(top_camera_id)

    if not side_camera or not top_camera:
        return False, "선택한 카메라를 찾을 수 없습니다. 카메라 목록을 새로 확인해 주세요."

    if not side_camera.get("dshow_device_name") or not top_camera.get("dshow_device_name"):
        return False, "선택한 카메라의 FFmpeg 장치 연결에 실패했습니다."

    # JSON 파일에 카메라 역할 설정 저장
    if not save_camera_config(side_camera_id, top_camera_id):
        return False, "카메라 설정 파일을 저장하지 못했습니다."

    # 저장한 설정을 현재 서버에도 즉시 적용
    success = apply_camera_config({
        "side_camera_id": side_camera_id,
        "top_camera_id": top_camera_id
    })

    if not success:
        return False, _camera_mapping_error or "카메라 설정을 적용하지 못했습니다."

    print("[카메라 설정 저장 완료]")
    return True, "카메라 설정이 저장되었습니다."

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
    global _available_cameras
    global _camera_mapping_error

    _cached_cameras = None
    _available_cameras = []
    _camera_mapping_error = None

    print("[카메라 자동 매칭] 메모리 정보 초기화 완료")

# ==========================================
# 카메라 매칭 오류 메시지 가져오기
# ==========================================
def get_camera_mapping_error():
    return _camera_mapping_error