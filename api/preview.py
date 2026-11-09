
from flask import Blueprint, jsonify, Response

import services.capture_service as capture_service
import services.preview_service as preview_service

from camera.discovery import get_cached_cameras


preview_bp = Blueprint("preview", __name__)


# ==========================================
# 카메라 미리보기 시작 API
# ==========================================
@preview_bp.route("/preview/start", methods=["POST"])
def start_preview():

    # 촬영 중에는 미리보기를 시작하지 않음
    if capture_service.is_running:
        return jsonify({
            "success": False,
            "message": "촬영 중에는 미리보기를 시작할 수 없습니다."
        }), 409

    # 카메라 자동 매칭 정보 확인
    detected_cameras = get_cached_cameras()

    if detected_cameras is None:
        return jsonify({
            "success": False,
            "message": "카메라 자동 매칭 정보가 초기화되지 않았습니다."
        }), 503

    # 미리보기 시작
    success, message, started_views = preview_service.start_preview(
        detected_cameras
    )

    if not success:
        return jsonify({
            "success": False,
            "message": message
        }), 409

    return jsonify({
        "success": True,
        "message": message,
        "started_views": started_views
    })


# ==========================================
# 카메라 미리보기 중지 API
# ==========================================
@preview_bp.route("/preview/stop", methods=["POST"])
def stop_preview():

    preview_service.stop_preview()

    return jsonify({
        "success": True,
        "message": "미리보기를 중지했습니다."
    })


# ==========================================
# 최신 미리보기 프레임 조회 API
# ==========================================
@preview_bp.route("/preview/frame/<view>", methods=["GET"])
def get_preview_frame(view):

    # Side / Top 이외의 요청은 거부
    if view not in ("side", "top"):
        return jsonify({
            "success": False,
            "message": "잘못된 카메라 구분입니다."
        }), 400

    # 최신 JPEG 프레임 가져오기
    frame = preview_service.get_preview_frame(view)

    # 아직 수신된 프레임이 없는 경우
    if frame is None:
        return Response(status=204)

    # JPEG 이미지 데이터 반환
    return Response(
        frame,
        status=200,
        mimetype="image/jpeg"
    )
