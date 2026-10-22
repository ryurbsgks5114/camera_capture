from flask_socketio import emit

# ==========================================
# WebSocket 테스트 이벤트 등록
# ==========================================
def register_socket_events(socketio):
    # GUI 앱이 WebSocket 서버에 성공적으로 연결되었을 때 실행되는 이벤트 핸들러
    @socketio.on("connect")
    def handle_connect(auth=None):
        print("[WebSocket] GUI 앱 연결")

        # 연결 직후 GUI 앱으로 "ws_test" 채널을 통해 테스트 메시지 데이터를 전송
        emit(
            "ws_test",
            {
                "type": "connection_test",
                "message": "WebSocket 테스트 이벤트 수신 성공"
            }
        )

    #  GUI 앱과 WebSocket 연결이 끊어졌을 때 실행되는 이벤트 핸들러
    @socketio.on("disconnect")
    def handle_disconnect(reason=None):
        print("[WebSocket] GUI 앱 연결 해제")
