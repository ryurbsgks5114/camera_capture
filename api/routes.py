from api.status import status_bp
from api.capture import capture_bp

def register_routes(app):
    app.register_blueprint(status_bp)
    app.register_blueprint(capture_bp)