import os
BASE_DIR = os.path.dirname(__file__)

SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'NNTT.db'))

SQLALCHEMY_TRACK_MODIFICATIONS = False

# 비밀키 추가: CSRF 토큰 생성
SECRET_KEY = "dev"