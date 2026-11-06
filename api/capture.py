
import config
import services.capture_service as capture_service
import threading
from camera.discovery import get_cached_cameras, get_camera_mapping_error
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from services.ftp_service import validate_ftp_connection
import services.preview_service as preview_service


capture_bp = Blueprint("capture", __name__)

# 촬영 시작 / 중지 API의 동시 접근 방지
capture_api_lock = threading.Lock()


# ==========================================
# 카메라 촬영 시작 API
# ==========================================
@capture_bp.route("/start", methods=["POST"])
def start_capture():

    # 요청 받은 JSON 데이터 파싱
    data = request.get_json(silent=True)

    if data is None:
        data = {}

    # ======================================
    # 촬영 시작 시간 검증
    # ======================================

    start_time_text = data.get("start_time")

    if not start_time_text:
        return jsonify({
            "success": False,
            "message": "촬영 시작 시간을 입력해야 합니다."
        }), 400

    try:
        start_time = datetime.strptime(
            start_time_text,
            "%H:%M:%S"
        ).time()

    except ValueError:
        return jsonify({
            "success": False,
            "message": "촬영 시작 시간은 HH:MM:SS 형식이어야 합니다."
        }), 400

    # ======================================
    # 촬영 간격 검증
    # ======================================

    interval_minutes = data.get(
        "interval_minutes",
        config.INTERVAL_MINUTES
    )

    try:
        interval_minutes = int(interval_minutes)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "촬영 간격은 숫자로 입력해야 합니다."
        }), 400

    if interval_minutes <= 0:
        return jsonify({
            "success": False,
            "message": "촬영 간격은 1분 이상이어야 합니다."
        }), 400

    # ======================================
    # 저장 방식 검증
    # ======================================

    storage_mode = data.get("storage_mode", "both")

    if storage_mode not in ("local", "ftp", "both"):
        return jsonify({
            "success": False,
            "message": "저장 방식이 올바르지 않습니다."
        }), 400

    # ======================================
    # 로컬 저장 경로
    # ======================================

    local_path = None

    if storage_mode in ("local", "both"):
        local_path = data.get("local_path")

    # ======================================
    # FTP 설정 검증
    # ======================================

    ftp_config = None

    if storage_mode in ("ftp", "both"):

        ftp_data = data.get("ftp")

        if not isinstance(ftp_data, dict):
            return jsonify({
                "success": False,
                "message": "FTP 설정이 필요합니다."
            }), 400

        required_fields = [
            "host",
            "port",
            "user",
            "password",
            "base_dir"
        ]

        for field in required_fields:

            if field not in ftp_data:
                return jsonify({
                    "success": False,
                    "message": "FTP 설정에 " + field + " 값이 필요합니다."
                }), 400

        try:
            ftp_port = int(ftp_data["port"])

        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "FTP 포트는 숫자로 입력해야 합니다."
            }), 400

        ftp_config = {
            "host": ftp_data["host"],
            "port": ftp_port,
            "user": ftp_data["user"],
            "password": ftp_data["password"],
            "base_dir": ftp_data["base_dir"]
        }

    # ======================================
    # 카메라 연결 상태 확인
    # ======================================

    detected_cameras = get_cached_cameras()

    if detected_cameras is None:
        return jsonify({
            "success": False,
            "message": "카메라 자동 매칭 정보가 초기화되지 않았습니다."
        }), 503

    mapping_error = get_camera_mapping_error()

    if mapping_error:
        return jsonify({
            "success": False,
            "message": "카메라 자동 매칭에 실패했습니다: " + mapping_error
        }), 503

    missing_cameras = []

    if not detected_cameras["side"]:
        missing_cameras.append("측면 카메라")

    if (
        getattr(config, "ENABLE_TOP_CAMERA", True)
        and not detected_cameras["top"]
    ):
        missing_cameras.append("상단 카메라")

    if missing_cameras:
        return jsonify({
            "success": False,
            "message": "카메라 연결을 확인해 주세요: " + ", ".join(missing_cameras)
        }), 503

    # ======================================
    # FTP 연결 확인
    # ======================================

    if storage_mode in ("ftp", "both"):

        ftp_valid, ftp_message = validate_ftp_connection(ftp_config)

        if not ftp_valid:
            return jsonify({
                "success": False,
                "message": ftp_message
            }), 503

    # ======================================
    # 촬영 시작 상태 확인 및 스레드 생성
    # ======================================

    with capture_api_lock:

        # 이미 촬영 중인 경우
        if capture_service.is_running:
            return jsonify({
                "success": False,
                "message": "촬영이 이미 실행 중입니다.",
                "interval_minutes": capture_service.current_interval_minutes
            }), 400

        # 이전 촬영 스레드가 아직 종료되지 않은 경우
        previous_thread = capture_service.capture_thread

        if (
            previous_thread is not None
            and previous_thread.is_alive()
        ):
            return jsonify({
                "success": False,
                "message": "이전 촬영 작업이 종료되는 중입니다. 잠시 후 다시 시도해 주세요."
            }), 409

        # 촬영 시작 전 미리보기 종료
        preview_service.stop_preview()

        # 백그라운드 서비스 상태 업데이트
        capture_service.is_running = True
        capture_service.current_interval_minutes = interval_minutes

        # WebSocket 객체 가져오기
        socketio = current_app.config.get("SOCKETIO")

        # 촬영 루프를 별도 데몬 스레드로 실행
        capture_service.capture_thread = threading.Thread(
            target=capture_service.capture_loop,
            args=(
                start_time,
                interval_minutes,
                storage_mode,
                ftp_config,
                socketio,
                local_path
            ),
            daemon=True
        )

        try:
            capture_service.capture_thread.start()

        except Exception as error:
            capture_service.is_running = False
            capture_service.current_interval_minutes = None
            capture_service.capture_thread = None

            print("[촬영 스레드 시작 실패]", error)

            return jsonify({
                "success": False,
                "message": "촬영 스레드를 시작하지 못했습니다."
            }), 500

    # ======================================
    # 촬영 시작 성공 응답
    # ======================================

    return jsonify({
        "success": True,
        "message": "촬영을 시작했습니다.",
        "start_time": start_time_text,
        "interval_minutes": interval_minutes,
        "storage_mode": storage_mode
    })


# ==========================================
# 카메라 촬영 중지 API
# ==========================================
@capture_bp.route("/stop", methods=["POST"])
def stop_capture():

    with capture_api_lock:

        capture_thread = capture_service.capture_thread

        # 이미 중지 요청이 전달된 상태
        if not capture_service.is_running:

            # 실제 스레드가 아직 정리 중이라면
            if (
                capture_thread is not None
                and capture_thread.is_alive()
            ):
                return jsonify({
                    "success": True,
                    "message": "촬영 종료 처리가 진행 중입니다."
                })

            return jsonify({
                "success": False,
                "message": "현재 촬영 중이 아닙니다."
            }), 400

        # 촬영 루프에 중지 요청 전달
        capture_service.is_running = False
        capture_service.current_interval_minutes = None

        print("========================================")
        print("촬영 중지 요청")
        print("========================================")

    return jsonify({
        "success": True,
        "message": "촬영 중지 명령을 전달했습니다."
    })
