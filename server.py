from flask import Flask, jsonify, request
import threading
import time
from datetime import datetime

from camera_capture import capture_cameras

app = Flask(__name__)

is_running = False
capture_thread = None
current_interval_minutes = None

# ==========================================
# 촬영 반복 작업
# ==========================================
def capture_loop(start_time, interval_minutes, storage_mode, ftp_config):

    global is_running

    print()
    print("========================================")
    print(" Camera Capture 프로그램 시작")
    print("========================================")
    print("촬영 예정 시간:", start_time)
    print("촬영 간격:", interval_minutes, "분")
    print("저장 방식:", storage_mode)
    print("========================================")

    # ======================================
    # 시작 시간 계산
    # ======================================
    now = datetime.now()

    target_time = datetime.combine(now.date(), start_time)

    if target_time <= now:
        next_capture_time = (time.monotonic())
    else:
        wait_seconds = (target_time - now).total_seconds()
        next_capture_time = (time.monotonic() + wait_seconds)

    interval_seconds = interval_minutes * 60

    while is_running:
        wait_seconds = (next_capture_time - time.monotonic())

        if wait_seconds > 0:
            # print("----------------------------------------")
            print("다음 촬영까지:", round(wait_seconds, 2), "초 대기합니다.")
            # print("----------------------------------------")

            while is_running:
                wait_seconds = (next_capture_time - time.monotonic())

                if wait_seconds <= 0:
                    break

                time.sleep(min(1, wait_seconds))
        if not is_running:
            break

        capture_cameras(storage_mode=storage_mode, ftp_config=ftp_config)

        next_capture_time += interval_seconds

        current_time = time.monotonic()

        if next_capture_time <= current_time:
            next_capture_time = (current_time + interval_seconds)

    print()
    print("========================================")
    print("촬영 작업 종료")
    print("========================================")

# ==========================================
# 상태 확인
# ==========================================
@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "server": "running",
        "capture": (
            "running"
            if is_running
            else "stopped"
        ),
        "interval_minutes":
            current_interval_minutes
    })

# ==========================================
# 촬영 시작
# ==========================================
@app.route("/start", methods=["POST"])
def start_capture():

    global is_running
    global capture_thread
    global current_interval_minutes

    if is_running:
        return jsonify({
            "success": False,
            "message":
                "촬영이 이미 실행 중입니다.",
            "interval_minutes":
                current_interval_minutes
        }), 400

    # --------------------------------------
    # JSON 데이터 확인
    # --------------------------------------
    data = request.get_json(silent=True)

    if data is None:
        data = {}

    # ======================================
    # 촬영 시작 시간
    # ======================================
    start_time_text = data.get("start_time")

    if not start_time_text:
        return jsonify({
            "success": False,
            "message":
                "촬영 시작 시간을 입력해야 합니다."
        }), 400

    try:
        start_time = datetime.strptime(start_time_text, "%H:%M:%S").time()
    except ValueError:
        return jsonify({
            "success": False,
            "message":
                "촬영 시작 시간은 HH:MM:SS 형식이어야 합니다."
        }), 400

    # --------------------------------------
    # 숫자 변환
    # --------------------------------------
    interval_minutes = data.get("interval_minutes", 1)

    try:
        interval_minutes = int(interval_minutes)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message":
                "촬영 간격은 숫자로 입력해야 합니다."
        }), 400

    # --------------------------------------
    # 촬영 간격 검증
    # --------------------------------------
    if interval_minutes <= 0:
        return jsonify({
            "success": False,
            "message":
                "촬영 간격은 1분 이상이어야 합니다."
        }), 400

    # ======================================
    # 저장 방식
    # ======================================
    storage_mode = data.get("storage_mode", "both")

    if storage_mode not in ("local", "ftp", "both"):
        return jsonify({
            "success": False,
            "message":
                "저장 방식이 올바르지 않습니다."
        }), 400

    # ======================================
    # FTP 설정
    # ======================================
    ftp_config = None

    if storage_mode in ("ftp", "both"):
        ftp_data = data.get("ftp")

        if not isinstance(ftp_data, dict):
            return jsonify({
                "success": False,
                "message":
                    "FTP 설정이 필요합니다."
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
                    "message":
                        "FTP 설정에 "
                        + field
                        + " 값이 필요합니다."
                }), 400

        try:
            ftp_port = int(ftp_data["port"])
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message":
                    "FTP 포트는 숫자로 입력해야 합니다."
            }), 400

        ftp_config = {
            "host":
                ftp_data["host"],
            "port":
                ftp_port,
            "user":
                ftp_data["user"],
            "password":
                ftp_data["password"],
            "base_dir":
                ftp_data["base_dir"]
        }

    # --------------------------------------
    # 상태 변경
    # --------------------------------------
    is_running = True

    current_interval_minutes = (interval_minutes)

    # --------------------------------------
    # 촬영 스레드 생성
    # --------------------------------------
    capture_thread = threading.Thread(
        target=capture_loop,
        args=(
            start_time,
            interval_minutes,
            storage_mode,
            ftp_config
        ),
        daemon=True
    )

    capture_thread.start()

    return jsonify({
        "success": True,
        "message":
            "촬영을 시작했습니다.",
        "start_time":
            start_time_text,
        "interval_minutes":
            interval_minutes,
        "storage_mode":
            storage_mode
    })

# ==========================================
# 촬영 중지
# ==========================================
@app.route("/stop", methods=["POST"])
def stop_capture():

    global is_running
    global current_interval_minutes

    if not is_running:
        return jsonify({
            "success": False,
            "message":
                "현재 촬영 중이 아닙니다."
        }), 400

    is_running = False

    current_interval_minutes = None

    print("========================================")
    print("촬영 중지 요청")
    print("========================================")

    return jsonify({
        "success": True,
        "message":
            "촬영 중지 명령을 전달했습니다."
    })

# ==========================================
# 서버 실행
# ==========================================
if __name__ == "__main__":
    print()
    print("========================================")
    print(" Camera Server 시작")
    print("========================================")
    print()
    print("종료하려면 Ctrl + C 를 누르세요.")
    print()

    app.run(host="0.0.0.0", port=5000)