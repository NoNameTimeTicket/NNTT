# 팝업 예매 & 가상 결제 백엔드 박근수 2026-08-06, 2026-08-07 현장판매, 사전판매관련 내용 수정

# C:\projects\NNTT\views\booking.py
from flask import Blueprint, render_template, request, redirect, url_for, g
from datetime import datetime

# 데이터베이스(DB) 연결 및 모델 가져오기
from init_db import db
from table_model import Reservation
from utils import extract_price_number, parse_kopis_times
import re # 글자 속에서 원하는 패턴(숫자)을 찾아내는 내는 함수

# 플라스크 블루프린트 설정 (/booking URL 관리)
booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

# =========================================================
#  새로 추가하는 코드
# 파일 아무 곳에서나 쓸 수 있게 popup() 함수 바로 위에 이 함수를 새로 추가
# 티켓가격 관련 함수
# =========================================================
def parse_ticket_prices(raw_price_str):
    if not raw_price_str:
        return[{'label': '일반', 'price': 0, 'text': '일반 (0원)'}]

    # "글자(좌석/종류) + 숫자 + 원" 패턴을 한꺼번에 모조리 찾음 (예: S석 20,000원)
    matches =re.findall(r'([가-힣a-zA-Z0-9\s]*?)\s*([\d,]+)\s*원', raw_price_str)

    options = []
    for label, price_str in matches:
        clean_label = label.strip() or '일반'
        price = int(price_str.replace(',', '')) # 쉼표(,) 빼고 숫자로 변경
        options.append({
            'label' : clean_label,
            'price' : price,
            'text' : f"{clean_label} ({price:,}원)" # 드롭다운 상자에 들어갈 글자
        })

    # 패턴 추출에 실패한 경우(숫자만 있는 경우 등) 예외 처리
    if not options:
        nums = re.findall(r'[\d,]+', raw_price_str)
        if nums:
            price = int(nums[0].replace(',', ''))
            options.append({'label': '일반', 'price': price, 'text': f"일반 ({price:,}원)"})
        else:
            options.append({'label': '무료 / 변동', 'price': 0, 'text': '무료 / 변동'})
    return options


# =========================================================
# 1. 팝업창 열릴 때 HTML로 데이터 전달해 주는 역할
# =========================================================
@booking_bp.route('/popup')
def popup():
    # 로그인 안 한 사용자는 팝업창 닫기
    if not hasattr(g, 'user') or not g.user:
        return "<script>alert('로그인이 필요한 서비스입니다.'); window.close();</script>"

    # 1) 상세페이지에서 보낸 공연 정보를 주소창(URL)에서 받아옵니다.
    performance_id = request.args.get('performance_id')
    title = request.args.get('title')
    place_name = request.args.get('place_name')
    address = request.args.get('address', '공연장 주소 미정')
    ticket_price_raw = request.args.get('ticket_price', '')
    dtguidance = request.args.get('time_notice', '')

    # 티켓가격 옵션관련
    ticket_options = parse_ticket_prices(ticket_price_raw)
    default_price = ticket_options[0]['price'] # 첫 번째 티켓 단가를 기본값으로 설정

    # 빠져있던 시간 파싱 및 오늘 날짜 만드는 코드
    available_times = parse_kopis_times(dtguidance) # 공연 회차 시간 목록
    today_date = datetime.now().strftime('%Y-%m-%d') # 오늘 날짜 (YYYY-MM-DD)

    # 3) HTML({{ data.xxx }})로 보낼 상자(data)를 포장합니다!
    popup_data = {
        'performance_id': performance_id,
        'title': title,
        'place_name': place_name,
        'address': address,
        'unit_price': default_price,
        'unit_price_text': f"{default_price:,}원", # 원화 표시 (예: 50,000원)
        'ticket_options' : ticket_options,        #티켓 가격 선택
        'available_times': available_times,     # 공연 시간 목록
        'today': today_date,                   # 오늘 날짜
        'user_phone': getattr(g.user, 'phone', '010-0000-0000') or '010-0000-0000'
    }

    # booking_popup.html 한테 popup_data를 'data'라는 이름으로 전달합니다!
    return render_template('booking_popup.html', data=popup_data)


# =========================================================
# 2. [가상 결제 완료하기] 버튼 누르면 DB에 예약 저장하는 역할
# =========================================================
@booking_bp.route('/pay_process', methods=['POST'])
def pay_process():
    if not hasattr(g, 'user') or not g.user:
        return "<script>alert('로그인이 필요합니다.'); window.close();</script>"

    # HTML 폼(form)에서 사용자가 선택한 값들을 받아옵니다.
    title = request.form.get('title')
    place_name = request.form.get('place_name')
    address = request.form.get('address', '공연장 주소')
    booking_date = request.form.get('booking_date')  # 달력에서 선택한 날짜
    booking_time = request.form.get('booking_time')  # 선택한 공연 시간
    ticket_count = request.form.get('ticket_count', '1') # 인원수

    if not booking_date or not booking_time:
        return "<script>alert('관람 날짜와 회차 시간을 선택해 주세요.'); history.back();</script>"

    # 날짜와 시간을 합쳐서 진짜 날짜 형식으로 변환합니다.
    try:
        target_datetime = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        target_datetime = datetime.now()

    full_place_info = f"{place_name} [{title} / {ticket_count}매]"

    # DB에 예매 정보 저장하기
    try:
        new_reservation = Reservation(
            username=g.user.username,
            address=address,
            place=full_place_info,
            reservation_date=target_datetime,
            is_canceled=False
        )
        db.session.add(new_reservation)
        db.session.commit()

        # 성공 알림창 띄우고 마이페이지로 이동 후 팝업 닫기
        return """
        <script>
            alert('🎉 공연 예매 및 가상결제가 성공적으로 완료되었습니다!\\n\\n마이페이지 예매 내역에서 티켓 확인증을 확인해보세요.');
            if (window.opener && !window.opener.closed) {
                window.opener.location.href = '/mypage/orders';
            }
            window.close();
        </script>
        """
    except Exception as error:
        db.session.rollback()
        print(f"결제 DB 저장 오류: {error}")
        return "<script>alert('예매 처리 중 오류가 발생했습니다.'); history.back();</script>"