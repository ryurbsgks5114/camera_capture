from flask import Flask
from flask_socketio import SocketIO
from api.routes import register_routes
from services.websocket_service import register_socket_events

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

# 라우트 등록
register_routes(app)

# WebSocket 이벤트 등록
register_socket_events(socketio)

if __name__ == "__main__":
    print()
    print("========================================")
    print(" Camera Server 시작")
    print("========================================")
    print()
    print("종료하려면 Ctrl + C 를 누르세요.")
    print()

    # Flask app.run() 대신 Socket.IO가 제공하는 실행 함수를 사용
    socketio.run(app, host="0.0.0.0", port=5000)