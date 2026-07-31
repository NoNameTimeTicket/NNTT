from flask import Flask
from routes import main_bp  # 작성하신 routes.py에서 main_bp를 가져옵니다.

app = Flask(__name__)

# 블루프린트 등록
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)