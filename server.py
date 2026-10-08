from flask import Flask
from api.routes import register_routes

app = Flask(__name__)

# 라우트 등록
register_routes(app)

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