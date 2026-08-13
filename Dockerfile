# 베이스 이미지 선택
FROM python:3.14-slim

# [수정] 시간대 설정 (KST)
# tzdata를 설치하고 환경 변수를 설정합니다.
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get clean

# 작업 디렉토리 생성 및 이동
WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# 전체 프로젝트 복사
COPY . .

# Flask 환경변수 설정
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 포트 오픈
EXPOSE 8080

# 앱 실행
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "app:create_app()"]