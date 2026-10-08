from flask import Blueprint, jsonify
import services.capture_service as capture_service

status_bp = Blueprint("status", __name__)

# 서버 및 촬영 상태 조회 API
@status_bp.route("/status", methods=["GET"])
def status():
    is_running = capture_service.is_running

    # 공통 반환 데이터 작성
    response_data = {
        "server": "running",
        "capture": "running" if is_running else "stopped"
    }

    # 촬영 중(running)일 때만 interval_minutes 키 추가
    if is_running:
        response_data["interval_minutes"] = capture_service.current_interval_minutes

    # JSON 응답 반환
    return jsonify(response_data)