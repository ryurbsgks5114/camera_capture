import threading
from datetime import datetime
from flask import Blueprint, jsonify, request
import services.capture_service as capture_service

capture_bp = Blueprint("capture", __name__)

# 카메라 촬영 시작 API
@capture_bp.route("/start", methods=["POST"])
def start_capture():
    # 이미 촬영이 실행 중인 경우 예외 처리
    if capture_service.is_running:
        return jsonify({
            "success": False,
            "message": "촬영이 이미 실행 중입니다.",
            "interval_minutes": capture_service.current_interval_minutes
        }), 400

    # 요청 받은 JSON 데이터 파싱
    data = request.get_json(silent=True)
    if data is None:
        data = {}

    # 촬영 시작 시간 검증
    start_time_text = data.get("start_time")
    if not start_time_text:
        return jsonify({
            "success": False,
            "message": "촬영 시작 시간을 입력해야 합니다."
        }), 400

    # HH:MM:SS 시간 형식 검증 및 datetime.time 객체 변환
    try:
        start_time = datetime.strptime(start_time_text, "%H:%M:%S").time()
    except ValueError:
        return jsonify({
            "success": False,
            "message": "촬영 시작 시간은 HH:MM:SS 형식이어야 합니다."
        }), 400

    # 촬영 간격 검증 (기본값: 1분 -> 나중에 10분 이런 기본값 변경 예정)
    interval_minutes = data.get("interval_minutes", 1)
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

    # 저장 방식(storage_mode) 값 유효성 검증 (local, ftp, both)
    storage_mode = data.get("storage_mode", "both")
    if storage_mode not in ("local", "ftp", "both"):
        return jsonify({
            "success": False,
            "message": "저장 방식이 올바르지 않습니다."
        }), 400

    # FTP 저장 방식일 경우 필수 설정값 검증
    ftp_config = None
    if storage_mode in ("ftp", "both"):
        ftp_data = data.get("ftp")
        if not isinstance(ftp_data, dict):
            return jsonify({
                "success": False,
                "message": "FTP 설정이 필요합니다."
            }), 400

        # FTP 필수 항목 존재 여부 확인
        required_fields = ["host", "port", "user", "password", "base_dir"]
        for field in required_fields:
            if field not in ftp_data:
                return jsonify({
                    "success": False,
                    "message": "FTP 설정에 " + field + " 값이 필요합니다."
                }), 400

        # FTP 포트 숫자 형태 검증
        try:
            ftp_port = int(ftp_data["port"])
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "FTP 포트는 숫자로 입력해야 합니다."
            }), 400

        # FTP 설정 객체 생성
        ftp_config = {
            "host": ftp_data["host"],
            "port": ftp_port,
            "user": ftp_data["user"],
            "password": ftp_data["password"],
            "base_dir": ftp_data["base_dir"]
        }

    # 백그라운드 서비스 상태 업데이트
    capture_service.is_running = True
    capture_service.current_interval_minutes = interval_minutes

    # 촬영 루프를 별도 데몬 스레드(Daemon Thread)로 실행
    capture_service.capture_thread = threading.Thread(
        target=capture_service.capture_loop,
        args=(
            start_time,
            interval_minutes,
            storage_mode,
            ftp_config
        ),
        daemon=True
    )
    capture_service.capture_thread.start()

    # 촬영 시작 성공 응답 반환
    return jsonify({
        "success": True,
        "message": "촬영을 시작했습니다.",
        "start_time": start_time_text,
        "interval_minutes": interval_minutes,
        "storage_mode": storage_mode
    })

# 카메라 촬영 중지 API
@capture_bp.route("/stop", methods=["POST"])
def stop_capture():
    # 이미 정지된 상태인 경우 예외 처리
    if not capture_service.is_running:
        return jsonify({
            "success": False,
            "message": "현재 촬영 중이 아닙니다."
        }), 400

    # 백그라운드 스레드 종료를 위한 플래그 변경 및 설정값 초기화
    capture_service.is_running = False
    capture_service.current_interval_minutes = None

    print("========================================")
    print("촬영 중지 요청")
    print("========================================")

    # 촬영 중지 요청 성공 응답 반환
    return jsonify({
        "success": True,
        "message": "촬영 중지 명령을 전달했습니다."
    })