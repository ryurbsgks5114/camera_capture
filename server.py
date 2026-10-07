from flask import Flask, jsonify, request
import threading
import time

from camera_capture import capture_cameras

app = Flask(__name__)

is_running = False
capture_thread = None
current_interval_minutes = None

# ==========================================
# 촬영 반복 작업
# ==========================================
def capture_loop(interval_minutes):

    global is_running

    print()
    print("========================================")
    print(" Camera Capture 프로그램 시작")
    print("========================================")
    print("촬영 간격:", interval_minutes, "분")
    print("========================================")

    interval_seconds = interval_minutes * 60

    next_capture_time = time.monotonic()

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

        capture_cameras()

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

    interval_minutes = data.get("interval_minutes", 1)

    # --------------------------------------
    # 숫자 변환
    # --------------------------------------
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
            interval_minutes,
        ),
        daemon=True
    )

    capture_thread.start()

    return jsonify({
        "success": True,
        "message":
            "촬영을 시작했습니다.",
        "interval_minutes":
            interval_minutes
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
    print(
        "종료하려면 Ctrl + C 를 누르세요."
    )
    print()

    app.run(host="0.0.0.0", port=5000)