# 팝업 예매 & 가상 결제 백엔드 박근수 2026-08-06

# C:\projects\NNTT\booking.py
from flask import Blueprint, render_template, request, redirect, url_for, g
from datetime import datetime

# 데이터베이스(DB) 연결 및 모델 가져오기
from init_db import db
from table_model import Reservation
from utils import extract_price_number, parse_kopis_times

# 플라스크 블루프린트 설정 (/booking URL 관리)
booking_bp = Blueprint('booking', __name__, url_prefix='/booking')


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

    # 2) 티켓 가격(숫자)과 공연 회차 시간(목록)을 정리합니다.
    unit_price = extract_price_number(ticket_price_raw)
    available_times = parse_kopis_times(dtguidance)
    today_date = datetime.now().strftime('%Y-%m-%d')

    # 3) HTML({{ data.xxx }})로 보낼 상자(data)를 포장합니다!
    popup_data = {
        'performance_id': performance_id,
        'title': title,
        'place_name': place_name,
        'address': address,
        'unit_price': unit_price,
        'unit_price_text': f"{unit_price:,}원", # 원화 표시 (예: 50,000원)
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