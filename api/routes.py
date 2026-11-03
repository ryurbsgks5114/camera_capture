from api.status import status_bp
from api.capture import capture_bp
from api.cameras import cameras_bp

# ==========================================
# 각 기능별 API 라우트 등록 함수
# ==========================================
def register_routes(app):
    # 서버 및 카메라 상태 조회 관련 API 등록(/status)
    app.register_blueprint(status_bp)
    # 카메라 촬영 제어 관련 API 등록(/start, /stop)
    app.register_blueprint(capture_bp)
    # 카메라 목록 조회 및 Side / Top 역할 설정 API 등록
    app.register_blueprint(cameras_bp)