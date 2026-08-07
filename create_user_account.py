from init_db import db
from app import create_app
from table_model import User

from werkzeug.security import generate_password_hash

# 1. Flask 애플리케이션 객체 생성
app = create_app()

number_count = 100

# 2. 애플리케이션 컨텍스트 내부에서 데이터베이스 작업 수행
with app.app_context():
    print("테스트 데이터 생성 시작...")

    # 암호는 54321 통일
    common_password_hash = generate_password_hash('54321')
    for i in range(number_count):
        num_str = f"{i:02d}"

        user_dummy = [
            User(
                username=f"user{num_str}",
                password=common_password_hash,
                email=f"test{i}@google.com",
                phone=f"010-4567-{i:04d}",  # 0000 ~ 0099
                address = f"부산 수영구 광안해변로 100 비치아파트 101동 {i+101}호"
            )
        ]
        db.session.bulk_save_objects(user_dummy)

    db.session.commit()
    print(f"Successfully created {number_count} dummy users!")
    
    pass_value = input("종료하려면 enter를 누르세요")
