from init_db import db
from sqlalchemy.orm import validates
import re
from sqlalchemy.dialects.mysql import INTEGER
from datetime import datetime

ADDRESS_LENGTH = 200
USERNAME_LENGTH = 150
MAX_STRING = 200

# 회원 정보
# username
#   unique = True 설정하여 중복을 막음
#   운영자용 계정은 가입못하게 설정
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    username = db.Column(db.String(USERNAME_LENGTH), unique=True, nullable=False)
    password = db.Column(db.String(MAX_STRING), nullable=False) # hashcode로 암호화하는 과정 때문에 여유 buffer 추가
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(ADDRESS_LENGTH), nullable=True)

    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now)

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
            raise ValueError('전화번호는 필수 입력 항목입니다.')

        # 숫자만 추출 ('-' 및 공백 제거)
        digits = re.sub(r'\D', '', str(phone_number))

        # 휴대폰 번호 패턴 검사 (010, 011, 016, 017, 018, 019로 시작하는 10자리 또는 11자리)
        # - 11자리 (01012345678): 010-1234-5678
        # - 10자리 (0111234567): 011-123-4567
        if len(digits) == 11 and digits.startswith(
            ('010', '011', '016', '017', '018', '019')
        ):
            formatted_phone = f'{digits[:3]}-{digits[3:7]}-{digits[7:]}'
        elif len(digits) == 10 and digits.startswith(
            ('010', '011', '016', '017', '018', '019')
        ):
            formatted_phone = f'{digits[:3]}-{digits[3:6]}-{digits[6:]}'
        else:
            raise ValueError(
                '올바른 휴대폰 번호 형식이 아닙니다. (예: 01012345678 또는 010-1234-5678)'
            )

        return formatted_phone

# 예약 정보
# 예약이 완료되고 나서 예약정보를 넣는다
class Reservation(db.Model):
    __tablename__ = 'reservation'

    # 예약 ID: unsigned 32bit (0 - 4,294,967,295) 약 42억개. AUTO_INCREMENT= id 자동증가
    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    # 예약자
    username = db.Column(db.String(USERNAME_LENGTH), nullable=False)
    # 예약 장소 주소
    address = db.Column(db.String(ADDRESS_LENGTH), nullable=False)
    # 예약 장소 이름
    place = db.Column(db.String(50), nullable=False)
    # 공연 제목
    title = db.Column(db.String(MAX_STRING), nullable=False)
    # 예약 시간
    reservation_date = db.Column(db.DateTime(), nullable=False)
    # 실제 공연 시간
    real_play_date = db.Column(db.DateTime(), nullable=False)
    # 취소 여부(기본 값= False)
    is_canceled = db.Column(db.Boolean, default=False, nullable=False)
    # 티켓 개수
    amount_ticket = db.Column(db.SmallInteger, nullable=False, default=1)
    # 총 결재 가격: unsigned 32bit (0 - 4,294,967,295) 음수 확률 0% unsigned 설정
    total_price = db.Column(INTEGER(unsigned=True), nullable=False, default=0)

    @validates('amount_ticket')
    def validate_amount_ticket(self, key, amount):
        if int(amount) > 100:
            raise ValueError('한 번에 예매할 수 있는 최대 티켓 수를 초과했습니다.')
        return amount

# 공지사항 글 
class Notice(db.Model):
    __tablename__ = 'notice'

    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    subject = db.Column(db.String(MAX_STRING), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    create_date = db.Column(db.DateTime(), nullable=False)
    updated_date = db.Column(db.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now)
    user_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('notice_set'))

# 자주 묻는 질문 글
class FAQ(db.Model):
    __tablename__ = 'faq'

    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    subject = db.Column(db.String(MAX_STRING), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    create_date = db.Column(db.DateTime(), nullable=False)
    updated_date = db.Column(db.DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now)
    user_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('faq_set'))