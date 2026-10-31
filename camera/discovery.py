import pythoncom
from comgrab3 import enumerate_cameras
from config import (SIDE_CAMERA_LOCATION_ID, TOP_CAMERA_LOCATION_ID)

# ==========================================
# USB 물리 경로 기반 촬영 가능 장치 검색 함수
# ==========================================
def find_camera_for_usb_path(path_key, cameras):
    # USB 물리 경로가 설정되지 않은 경우 검색 종료
    if not path_key:
        return None

    # 전달받은 USB 물리 경로와 일치하는 카메라 검색
    for camera in cameras:
        camera_location_id = camera.get("location_id", "")

        if camera_location_id.lower() == path_key.lower():
            print("[카메라 인식] 장치 발견:", path_key, "->", camera["name"], "(index:", camera["index"], ")")

            return camera

    print("[카메라 인식] 장치를 찾지 못했습니다:", path_key)

    return None

# ==========================================
# 측면 및 탑 카메라 전체 탐색 함수
# ==========================================
def discover_cameras():
    try:
        # Windows COM 초기화
        pythoncom.CoInitialize()

        # 연결된 카메라 장치 목록 조회
        cameras = enumerate_cameras()

        # USB 물리 경로를 기준으로 측면 및 탑 카메라 검색
        side_camera = find_camera_for_usb_path(SIDE_CAMERA_LOCATION_ID, cameras)
        top_camera = find_camera_for_usb_path(TOP_CAMERA_LOCATION_ID, cameras)

        return {
            "side": side_camera,
            "top": top_camera
        }
    finally:
        # Windows COM 초기화 해제
        pythoncom.CoUninitialize()