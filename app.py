from flask import Flask
from routes import main_bp  # main_bp를 가져옵니다.
import config
from init_db import db, migrate  # init_db에서 db 생성자 내용 가져온다
from views import auth_views
from views.support import notice_views, faq_views
from filter.filter_date import format_datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app) # db 초기화
    migrate.init_app(app, db) # app과 db를 연결한다

    # 블루프린트 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_views.bp)  # auth_views 파일 안의 'bp' 객체 등록
    app.register_blueprint(notice_views.bp)
    app.register_blueprint(faq_views.bp)

    # jinja_env 필터에 등록
    app.jinja_env.filters['datetime'] = format_datetime

    return app

if __name__ == '__main__':
    app = create_app()
    # py app.py 실행 코드
    app.run(debug=True)