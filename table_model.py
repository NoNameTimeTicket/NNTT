from init_db import db
from sqlalchemy.orm import validates
import re
from filter.filter_date import format_datetime

address_length = 200
username_length = 150
max_string = 200

# 회원 정보
# username
#   unique = True 설정하여 중복을 막음
#   운영자용 계정은 가입못하게 설정
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(username_length), unique=True, nullable=False)
    password = db.Column(db.String(max_string), nullable=False) # hashcode로 암호화하는 과정 때문에 여유 buffer 추가
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(address_length), nullable=True)

    #금지된 username 검증
    @validates('username')
    def validate_username(self, key, username):
        # 금지어 목록 (소문자로 변환해서 비교하기 위해 소문자로 작성)
        forbidden_usernames = ['noname', 'admin', 'root', 'null', 'undefined']
        
        # 대소문자 구분 없이 체크 (e.g., 'NoName', 'NONAME' 모두 방지)
        if username.strip().lower() in forbidden_usernames:
            raise ValueError(f"'{username}'은(는) 사용할 수 없는 사용자 이름입니다.")
        
        return username

    @validates('phone')
    def validate_phone(self, key, phone_number):
        if not phone_number:
            return phone_number  # nullable=True 인 경우 빈 값 허용

        # 010-1234-5678 또는 02-123-4567 형태 검사 (하이픈 포함)
        # ^0\d{1,2}-\d{3,4}-\d{4}$ -> 0으로 시작, 국번 2~3자리, 중간 3~4자리, 끝 4자리
        pattern = r'^0\d{1,2}-\d{3,4}-\d{4}$'
        
        if not re.match(pattern, phone_number):
            raise ValueError("올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)")
            
        return phone_number

# 예약 정보
# 예약이 완료되고 나서 예약정보를 넣는다
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 예약자
    username = db.Column(db.String(username_length), nullable=False)
    # 예약 주소
    address = db.Column(db.String(address_length), nullable=False)
    # 예약 장소이름
    place = db.Column(db.String(50), nullable=False)
    # 예약 시간
    reservation_date = db.Column(db.DateTime(), nullable=False)
    # 취소 여부(기본 값= False)
    is_canceled = db.Column(db.Boolean, default=False, nullable=False)

# 공지사항 글 
class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(max_string), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    create_date = db.Column(db.DateTime(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('notice_set'))

# 자주 묻는 질문 글
class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(max_string), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    create_date = db.Column(db.DateTime(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('faq_set'))