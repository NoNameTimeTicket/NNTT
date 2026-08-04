from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# DB 생성자
db = SQLAlchemy()
# 관리자
migrate = Migrate()