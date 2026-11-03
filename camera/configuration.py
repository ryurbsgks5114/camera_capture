import json
import os
from pathlib import Path

# 사용자 PC별 카메라 역할 설정 저장 폴더
USER_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CameraCapture"

# 사용자 PC에서 지정한 카메라 역할 설정 파일
CAMERA_CONFIG_FILE = USER_DATA_DIR / "camera_config.json"

# ==========================================
# 저장된 카메라 역할 설정 불러오기
# ==========================================
def load_camera_config():
    if not CAMERA_CONFIG_FILE.exists():
        return None

    try:
        with CAMERA_CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return None

        side_camera_id = data.get("side_camera_id")
        top_camera_id = data.get("top_camera_id")

        if not isinstance(side_camera_id, str) or not side_camera_id.strip():
            return None

        if not isinstance(top_camera_id, str) or not top_camera_id.strip():
            return None

        if side_camera_id == top_camera_id:
            return None

        return {
            "side_camera_id": side_camera_id,
            "top_camera_id": top_camera_id
        }
    except (OSError, json.JSONDecodeError):
        return None

# ==========================================
# 카메라 역할 설정을 JSON 파일에 저장
# ==========================================
def save_camera_config(side_camera_id, top_camera_id):
    data = {
        "side_camera_id": side_camera_id,
        "top_camera_id": top_camera_id
    }

    try:
        # 사용자 설정 폴더가 없는 경우 자동 생성
        CAMERA_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

        with CAMERA_CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True
    except OSError as error:
        print("[카메라 설정 저장 실패]", error)
        return False