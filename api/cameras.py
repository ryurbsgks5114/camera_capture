from flask import Blueprint, jsonify, request
from camera.discovery import get_available_cameras, get_saved_camera_config, configure_cameras

cameras_bp = Blueprint("cameras", __name__)

# ==========================================
# 연결된 카메라 목록 조회 API
# ==========================================
@cameras_bp.route("/cameras", methods=["GET"])
def cameras():
    available_cameras = get_available_cameras()

    camera_list = []

    for index, camera in enumerate(available_cameras, start=1):
        camera_list.append({
            "id": camera.get("location_id", ""),
            "name": camera.get("name", ""),
            "location_id": camera.get("location_id", ""),
            "available": bool(camera.get("dshow_device_name"))
        })

    return jsonify({
        "success": True,
        "cameras": camera_list
    })

# ==========================================
# 저장된 카메라 역할 설정 조회 API
# ==========================================
@cameras_bp.route("/camera-config", methods=["GET"])
def get_camera_config():
    camera_config = get_saved_camera_config()

    if not camera_config:
        return jsonify({
            "success": True,
            "configured": False,
            "camera_config": None
        })

    return jsonify({
        "success": True,
        "configured": True,
        "camera_config": camera_config
    })

# ==========================================
# Side / Top 카메라 역할 설정 저장 API
# ==========================================
@cameras_bp.route("/camera-config", methods=["POST"])
def save_camera_config():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "카메라 설정 데이터가 올바르지 않습니다."
        }), 400

    side_camera_id = data.get("side_camera_id")
    top_camera_id = data.get("top_camera_id")

    if not isinstance(side_camera_id, str) or not side_camera_id.strip():
        return jsonify({
            "success": False,
            "message": "측면 카메라를 선택해 주세요."
        }), 400

    if not isinstance(top_camera_id, str) or not top_camera_id.strip():
        return jsonify({
            "success": False,
            "message": "상단 카메라를 선택해 주세요."
        }), 400

    success, message = configure_cameras(side_camera_id, top_camera_id)

    if not success:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "camera_config": {
            "side_camera_id": side_camera_id,
            "top_camera_id": top_camera_id
        }
    })