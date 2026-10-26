# ==========================================
# WebSocket 연결 이벤트 등록
# ==========================================
def register_socket_events(socketio):
    # GUI 앱이 WebSocket 서버에 성공적으로 연결되었을 때 실행되는 이벤트 핸들러
    @socketio.on("connect")
    def handle_connect(auth=None):
        print("[WebSocket] GUI 앱 연결")

    #  GUI 앱과 WebSocket 연결이 끊어졌을 때 실행되는 이벤트 핸들러
    @socketio.on("disconnect")
    def handle_disconnect(reason=None):
        print("[WebSocket] GUI 앱 연결 해제")
