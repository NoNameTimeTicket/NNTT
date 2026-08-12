# 팝업 예매 & 가상 결제 백엔드 박근수 2026-08-06, 2026-08-07 현장판매, 사전판매관련 내용 수정

from flask import Blueprint, render_template, request, redirect, url_for, g
from datetime import datetime
import requests
# 데이터베이스(DB) 연결 및 모델 가져오기
from init_db import db
from table_model import Reservation
from utils import parse_kopis_times
import re # 글자 속에서 원하는 패턴(숫자)을 찾아내는 내는 함수

# 플라스크 블루프린트 설정 (/booking URL 관리)
booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

# 카드 결제를 역할 서버 주소
PAYMENT_SERVER_URL = "http://127.0.0.1:8000/api/v1/payment"

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
# ★ [신규] 공연 요일 문구("토요일 ~ 일요일")를 숫자("0,6")로 변환하는 함수
# (0=일요일, 1=월요일, 2=화요일, 3=수요일, 4=목요일, 5=금요일, 6=토요일)
# =========================================================
def parse_allowed_days(notice_text):
    # [1단계] 안내 문구가 비어있거나 없으면 모든 요일(일~토)을 다 선택할 수 있게 합니다
    if not notice_text:
        return "0, 1, 2, 3, 4, 5, 6" # 기본값: 전 요일 허용

    # [2단계] 요일 이름을 숫자로 바꾸기 위한 기준 배열과 허용할 요일을 담을 주머니(set) 준비
    day_names = ['일', '월', '화', '수', '목', '금', '토']
    allowed = set() # 중복을 자동으로 막아주는 집합(Set) 주머니입니다.

    # [3단계] "X요일 ~ Y요일" 형태의 범위 문구 찾기 (예: "토요일 ~ 일요일", "화 ~ 금")
    # 정규식 설명: 요일 이름 + '요일' 글자(생략가능) + 물결(~) + 요일 이름
    match = re.search(r'([일월화수목금토])요일?\s*~\s*([일월화수목금토])요일?', notice_text)
 
    if match:
        # 시작 요일과 끝 요일의 숫자 위치(인덱스)를 알아냅니다.
        # 예: '토' -> 6, '일' -> 0
        start_idx = day_names.index(match.group(1))
        end_idx = day_names.index(match.group(2))

        curr = start_idx
        while True:
            allowed.add(curr) # 현재 요일 숫자를 주머니에 넣습니다.
            if curr == end_idx:
                break # 끝 요일까지 다 넣었으면 반복을 멈춥니다.
            curr = (curr + 1) % 7 # 토요일(6) 다음은 7이 아니라 0(일요일)으로 되돌아가게 돌립니다.

    # ★ 추가 단일 요일(예: "토요일", "일요일") 개별 추출해서 주머니에 다 담기
    single_days = re.findall(r'([일월화수목금토])요일?', notice_text)
    for day in single_days:
        allowed.add(day_names.index(day)) # '토'(6), '일'(0)도 빠짐없이 주머니에 담김

    # [4단계] 문구 속에 '평일'이나 '주말'이라는 단어가 들어있는지 체크합니다.
    if '평일' in notice_text:
        allowed.update([1, 2, 3, 4, 5]) # 월(1) ~ 금(5) 추가
    if '주말' in notice_text:
        allowed.update([0, 6]) # 일(0), 토(6) 추가

    # [5단계] 문 분석을 거쳤는데도 뽑아낸 요일이 하나도 없다면, 안전하게 전 요일을 허용합니다.
    if not allowed:
        return "0, 1, 2, 3, 4, 5, 6"

    # [6단계] 주머니에 모인 숫자를 순서대로 정렬한 뒤, 자바스크립트가 쓰기 좋게 "0,6" 문자열로 만듭니다.
    # 예: {6, 0} -> [0, 6] -> "0,6"
    return ",".join(map(str, sorted(list(allowed))))


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

    # URL에서 KOPIS 공연 기간 받아와서 점(.)을 하이픈(-)으로 변경
    raw_start = request.args.get('start_date', today_date).replace('.', '-').strip()
    raw_end = request.args.get('end_date', today_date).replace('.', '-').strip()

    # 오늘 날짜와 공연 시작일 중 더 나중 날짜를 start_date로 선택 (과거 날짜 차단!)
    start_date = max(today_date, raw_start)
    end_date = raw_end

    if end_date < start_date:
        end_date = start_date

    allowed_days = parse_allowed_days(dtguidance)

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
        'start_date': start_date, # ★ 달력 시작일 (오늘 이전 과거 날짜는 자동 제외됨)
        'end_date': end_date, # ★ 달력 종료일 (공연 끝나는 날)
        'allowed_days' : allowed_days, # 달력요일
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
    ticket_count = int(request.form.get('ticket_count', '1')) # 인원수    
    unit_price = int(request.form.get('unitPrice', 0)) # 티켓 한장 가격    
    total_price = unit_price * ticket_count

    # 계산 버튼을 누르면 얻는 정보
    print("-----예약 정보-----")
    print(f'제목 = {title}')
    print(f'공연장소 = {place_name}')
    print(f'공연장소 주소 = {address}')
    print(f'booking_date = {booking_date}')
    print(f'booking_time = {booking_time}')
    print(f'ticket_count = {ticket_count}')
    print(f'unit_price = {unit_price}')
    print(f'total_price = {total_price}')
    print("---------------")

    if not booking_date or not booking_time:
        return "<script>alert('관람 날짜와 회차 시간을 선택해 주세요.'); history.back();</script>"

    # 날짜와 시간을 합쳐서 진짜 날짜 형식으로 변환합니다.
    try:
        target_datetime = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        target_datetime = datetime.now()

    # DB에 예매 정보 저장하기
    try:
        new_reservation = Reservation(
            username=g.user.username,
            address=address,
            place=place_name,
            title = title,
            reservation_date=datetime.now(),
            real_play_date = target_datetime,
            is_canceled=False,
            amount_ticket= ticket_count,
            total_price= total_price
        )

        # FastAPI 서버로 결재 정보 파라미터 설정
        payload_to_server = {
            "user_id": g.user.username,
            "price": total_price,
            "reservation_date" : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        response = requests.post(PAYMENT_SERVER_URL, json=payload_to_server, timeout=5)

        json_status_value = response.json().get("status")
        print(f"response.status_code = {response.status_code}")        
        print(f"response.json().get(status) = {json_status_value}")

        if response.status_code == 200 and json_status_value == "APPROVED":
            # 결제 성공시에만 DB 커밋
            db.session.add(new_reservation)
            db.session.commit()
            return """<script>
                    alert('공연 예매 및 가상결제가 성공적으로 완료되었습니다!');
                    if (window.opener && !window.opener.closed) {
                        window.opener.location.href = '/booking/orders';
                    }
                    window.close();
                </script>"""
        else:
            # 결제 실패 시 DB 롤백
            db.session.rollback()
            return "<script>alert('결제에 실패했습니다. 다시 시도해주세요.'); history.back();</script>"

    except requests.exceptions.RequestException as e:
        # 네트워크/서버 통신 에러 처리
        db.session.rollback()
        return "<script>alert('결제 서버와 통신 중 에러가 발생했습니다'); history.back();</script>"
    
    except Exception as error:
        db.session.rollback()
        print(f"결제 DB 저장 오류: {error}")
        return "<script>alert('예매 처리 중 오류가 발생했습니다.'); history.back();</script>"


# =========================================================
# 내 예매 내역 목록 보기 (월별 검색 드롭다운 포함)
# =========================================================
@booking_bp.route('/orders')
def my_orders():
    # 1. 로그인 안 한 사용자는 로그인 페이지로 이동
    if not hasattr(g, 'user') or not g.user:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    # 2. 드롭다운에서 선택한 월 (예: '2026-08') 가져오기
    selected_month = request.args.get('month', '')

    try:
        # 3. 현재 사용자의 전체 예매 내역을 최신순으로 가져오기
        user_reservation = Reservation.query.filter_by(username=g.user.username)\
                                            .order_by(Reservation.id.desc()).all()

        # 4. 드롭다운 선택상자용 (년-월) 목록 중복 없이 만들기
        available_months = sorted(list({
            item.real_play_date.strftime('%Y-%m')
            for item in user_reservation if item.real_play_date
        }), reverse=True)

        # 5. 월을 선택했다면 해당 월의 내역만 필터링
        if selected_month:
            year_num, month_num = map(int, selected_month.split('-'))
            user_reservation = [
                item for item in user_reservation
                if item.real_play_date and
                   item.real_play_date.year == year_num and
                   item.real_play_date.month == month_num
            ]
    except Exception as error:
        print(f"예매 내역 조회 오류: {error}")
        user_reservation = []
        available_months = []

    # 6. 간단해진 예매 목록(user_reservations)을 HTML로 전달
    return render_template(
        'orders.html',
        orders=user_reservation,
        available_months=available_months,
        selected_month=selected_month
    )

# =========================================================
# 예매 취소 기능 (DB 삭제 대신 취소 상태만 변경)
# =========================================================
@booking_bp.route('/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if not hasattr(g, 'user') or not g.user:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    # 취소할 예매 내역 찾기
    target_order = Reservation.query.filter_by(id=order_id, username=g.user.username).first()

    if not target_order:
        return "<script>alert('해당 예매 내역을 찾을 수 없습니다.'); history.back();</script>"

    if target_order.is_canceled:
        return "<script>alert('이미 취소된 예매 건입니다.'); history.back();</script>"

    try:
        # DB에서 아예 지우지(delete) 않고, 취소 여부만 참(True)으로 바꿈
        target_order.is_canceled = True
        db.session.commit()
        return "<script>alert('예매가 취소되었습니다.'); location.href='/booking/orders';</script>"

    except Exception as error:
        db.session.rollback()
        print(f"예매 취소 오류: {error}")
        return "<script>alert('예매 취소 중 오류가 발생했습니다.'); history.back();</script>"