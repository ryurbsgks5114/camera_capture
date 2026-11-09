from flask import Blueprint, jsonify, request
from camera.discovery import (
    refresh_available_cameras,
    get_saved_camera_config,
    configure_cameras
)

cameras_bp = Blueprint("cameras", __name__)


# ==========================================
# Get connected cameras
# ==========================================
@cameras_bp.route("/cameras", methods=["GET"])
def cameras():
    try:
        # Perform a real device scan on every list refresh request
        camera_list = refresh_available_cameras()

        return jsonify({
            "success": True,
            "cameras": camera_list
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": "카메라 검색에 실패했습니다: " + str(error)
        }), 500


# ==========================================
# Get saved camera role configuration
# ==========================================
@cameras_bp.route("/camera-config", methods=["GET"])
def get_camera_config():
    camera_config = get_saved_camera_config()

    return jsonify({
        "success": True,
        "configured": bool(camera_config),
        "camera_config": camera_config
    })


# ==========================================
# Save Side / Top camera role configuration
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

    success, message = configure_cameras(
        side_camera_id,
        top_camera_id
    )

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