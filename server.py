import atexit
from flask import Flask
from flask_socketio import SocketIO
from api.routes import register_routes
from services.websocket_service import register_socket_events
from camera.discovery import (initialize_camera_mapping, clear_camera_mapping)

app = Flask(__name__)

# HTTP API와 WebSocket을 같은 포트에서 제공
# threading 모드를 사용하므로 기존 촬영 스레드 구조를 유지
socketio = SocketIO(
    app,
    async_mode="threading",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# 촬영 API에서 사용할 수 있도록 Socket.IO 객체 등록
app.config["SOCKETIO"] = socketio

# 라우트 등록
register_routes(app)

# WebSocket 이벤트 등록
register_socket_events(socketio)

# 서버 종료 시 카메라 매칭 정보 초기화
atexit.register(clear_camera_mapping)

if __name__ == "__main__":
    print()
    print("========================================")
    print(" Camera Server 시작")
    print("========================================")
    print()
    print("종료하려면 Ctrl + C 를 누르세요.")
    print()

    # 서버 시작 시 카메라 검색 및 FFmpeg 장치명 자동 매칭
    initialize_camera_mapping()

    try:
        # Flask app.run() 대신 Socket.IO가 제공하는 실행 함수를 사용(reloader를 끄고 카메라 자동 매칭이 중복 실행되지 않도록 함)
        socketio.run(app, host="0.0.0.0", port=5000, use_reloader=False)
    finally:
        # 서버 실행 함수가 종료되면 카메라 정보 초기화
        clear_camera_mapping()