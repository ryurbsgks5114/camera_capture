from api.status import status_bp
from api.capture import capture_bp
from api.photos import photos_bp

# ==========================================
# 각 기능별 API 라우트 등록 함수
# ==========================================
def register_routes(app):
    # 서버 및 카메라 상태 조회 관련 API 등록(/status)
    app.register_blueprint(status_bp)
    # 카메라 촬영 제어 관련 API 등록(/start, /stop)
    app.register_blueprint(capture_bp)
    # 촬영 사진 다운로드 API 등록(/photos/<date>/<filename>)
    app.register_blueprint(photos_bp)