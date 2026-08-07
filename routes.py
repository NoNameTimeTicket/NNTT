from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, abort, jsonify
import requests, re
import xml.etree.ElementTree as ET
from forms import UserCreateForm
from flask import render_template, request
from concurrent.futures import ThreadPoolExecutor, as_completed

main_bp = Blueprint('main', __name__)
KOPIS_API_KEY = "19fc20e402ce49df83b5d2f6e9d50822"

# def get_kopis_performances():
def get_kopis_performances(prfstate='02', rows='50', keyword=None, kid=None, shcate=None):
    """KOPIS API를 호출하여 전체 공연 목록 또는 검색 결과를 가져오는 공통 함수"""

    # 오늘 날짜 및 종료일(예: 오늘부터 180일 후) 동적 생성
    today = datetime.now()
    stdate_str = today.strftime('%Y%m%d')                        
    eddate_str = (today + timedelta(days=180)).strftime('%Y%m%d')
    print(f"시작날짜: {stdate_str}, 종료날짜: {eddate_str}")

    url = "http://www.kopis.or.kr/openApi/restful/pblprfr"
    params = {
        'service': KOPIS_API_KEY,
        'stdate': stdate_str,
        'eddate': eddate_str,
        'cpage': '1',
        'rows': str(rows),
        'prfstate': prfstate
    }
    # kid 파라미터가 들어오면 요청값에 추가 (아동공연 전용)
    if kid:
        params['kid'] = kid

    # 장르코드가 들어오면 요청값에 추가
    if shcate:
        params['shcate'] = shcate

    # 검색어(keyword)가 전달되었을 때만 shprfnm 파라미터 추가
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        performances = []
        for db in root.findall('db'):
            prfnm = db.findtext('prfnm') or ''
            area = db.findtext('area') or ''

             # 검색어가 들어온 경우: 공연명(prfnm)에도 없고 지역명(area)에도 없으면 제외
            if keyword and (keyword.strip() not in prfnm and keyword.strip() not in area):
                continue

            performances.append({
                'mt20id': db.findtext('mt20id'), # KOPIS 고유 공연 ID
                'prfnm': prfnm,                  # 공연 제목 (공연명)
                'genrenm': db.findtext('genrenm'), # 장르명 (예: 뮤지컬, 연극, 콘서트 등
                'area' : area,                   # 지역명 (예: 서울, 대구, 경기 등)
                'prfpdfrom': db.findtext('prfpdfrom'), # 공연 시작일 (YYYY.MM.DD)
                'prfpdto': db.findtext('prfpdto'), # 공연 종료일 (YYYY.MM.DD)
                'poster': db.findtext('poster'),   # 메인 포스터 이미지 URL
                'fcltynm': db.findtext('fcltynm')  # 공연장/시설 명칭 (예: 세종문화회관)
            })
        return performances
    except Exception as e:
        print(f"API 요청 실패: {e}")
        return []

# 메인 (통합검색 + 상단 GNB + 장르별 탭 + 공연 목록)
# 박근수 수정 2026-08-05
@main_bp.route('/')
def index():
    search_query = request.args.get('q', '').strip() # 검색어 수집
    genre_tab = request.args.get('genre', 'all') # 장르 탭 수집

    
    # 검색어(search_query)를 넣어서 KOPIS API 호출    
    if search_query:
        performances = get_kopis_performances(keyword=search_query) 
        # search.html에 performances=performances 추가   
        return render_template('search.html', query=search_query, performances=performances)
    

    # 검색어가 없는 일반 메인 접속 -> index.html 렌더링    
    return render_template('index.html', query='', current_genre=genre_tab)

def parse_date(perf):
    """'2026.08.01' 또는 '2026-08-01' 형태의 날짜를 datetime으로 변환하는 함수"""
    date_str = perf.get('prfpdfrom', '').replace('.', '-').strip()
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return datetime.max

# 💡 공통 데이터 로직 함수 생성
def get_sorted_upcoming_performances(limit=None):
    """KOPIS에서 공연 예정 데이터를 가져와 정렬 후 지정된 개수만큼 반환"""
    raw_perfs = get_kopis_performances(prfstate='01', rows='50')
    sorted_perfs = sorted(raw_perfs, key=parse_date)
    
    if limit:
        return sorted_perfs[:limit]
    return sorted_perfs

@main_bp.route('/api/upcoming')
def api_upcoming_performances():
    # 공통 함수 사용 (상위 5개만)
    upcoming_5 = get_sorted_upcoming_performances(limit=5)
    return jsonify(upcoming_5)

@main_bp.route('/performances/upcoming')
def upcoming_performances():
    # 공통 함수 사용 (전체 50개)
    upcoming_all = get_sorted_upcoming_performances()
    return render_template('upcoming_list.html', performances=upcoming_all)
    

# 전체 공연 목록 페이지
@main_bp.route('/performances/all')
def all_performances():
    performances = get_kopis_performances()
    return render_template('all_list.html', performances=performances)

# 뮤지컬 전용 페이지
@main_bp.route('/performances/musical')
def musical_list():
    all_perfs = get_kopis_performances()
    musicals = [p for p in all_perfs if p.get('genrenm') == '뮤지컬']
    return render_template('musical.html', performances=musicals)

# 콘서트 목록 페이지
@main_bp.route('/performances/concert')
def concert_list():
    all_perfs = get_kopis_performances()
    # KOPIS에서 대중음악/대중콘서트/음악 등으로 들어올 수 있어 포함 여부 체크
    concerts = [p for p in all_perfs if '콘서트' in p.get('genrenm', '') or '음악' in p.get('genrenm', '')]
    return render_template('concert.html', performances=concerts)

# 연극 전용 페이지
@main_bp.route('/performances/play')
def play_list():
    all_perfs = get_kopis_performances()
    plays = [p for p in all_perfs if p.get('genrenm') == '연극']
    return render_template('play.html', performances=plays)

# 박근수 추가 2026-08-05
# 아동/가족 전용 페이지
@main_bp.route('/performances/kids')
def kids_list():
    kids_perfs = get_kopis_performances(kid='Y')
    return render_template('kids.html', performances=kids_perfs)

# 클래식 전용 페이지 (KOPIS 장르코드 CCCA: 서양음악/클래식)
@main_bp.route('/performances/classic')
def classic_list():
    class_perfs = get_kopis_performances(shcate='CCCA')
    return render_template('classic.html', performances=class_perfs)

# 전시 전용 페이지 (KOPIS 장르코드 EEEA: 전시)
@main_bp.route('/performances/exhib')
def exhib_list():
    exhib_perfs = get_kopis_performances(shcate='EEEA')
    return render_template('exhib.html', performances=exhib_perfs)

# 2. 공연 상세 (공통 상세페이지 + 회차 예매 모달 + 공연 후기 게시판)
# 1) 상세페이지 수정 2026-08-04 박근수
@main_bp.route('/performances/<string:perf_id>')
def performance_detail(perf_id):
    #수정버젼 2026-08-04 박근수, 2026-08-04 간결한 코딩 및 날짜 수정
    
    try:
        # 1. 공연 상세 API 호출
        url = f"http://www.kopis.or.kr/openApi/restful/pblprfr/{perf_id}"
        res = requests.get(url, params={'service': KOPIS_API_KEY}, timeout=5)

        #2. KOPIS 서버 응답 에러 처리
        if res.status_code !=200:
            print(f"[상세 API 호출 실패] 공연 ID: {perf_id} | HTTP 상태 코드: {res.status_code}")
            abort(500, description="KOPIS API 호출에 실패했습니다.")

        root = ET.fromstring(res.content)
        db = root.find('db')

        # 3. KOPIS에 해당 공연 정보가 존재하지 않는 경우
        if db is None:
            print(f"[상세 조회 실패] 공연 ID: {perf_id} 정보를 데이터베이스에서 찾을 수 없음")
            abort(404, description="해당 공연 정보를 찾을 수 없습니다.")

        #4. XML 태그 안전 추출 헬퍼 함수
        get_txt = lambda tag: (db.findtext(tag) or '').strip()     

        # 변수 사전 초기화로 UnboundLocalError 예방
        address = ''
        district_location = ''       

        # [prfplcDetailRequest] 공연시설 상세 API에서 adres(도로명 주소) 추출
        fclty_id = get_txt('fcltyid')
        address = ''
        if fclty_id:
            try:
                f_url = f"http://www.kopis.or.kr/openApi/restful/prfplc/{fclty_id}"
                f_res = requests.get(f_url, params={'service': KOPIS_API_KEY}, timeout=3)
                if f_res.status_code == 200:
                    f_root = ET.fromstring(f_res.content)

                    # [수정] 오타 수정 (fetched_adres로 변수 안전 처리)
                    fetched_adres =f_root.findtext('.//adres')
                    if fetched_adres and fetched_adres.strip():
                        address = fetched_adres.strip()
                    else:
                        print(f"[KOPIS DB] 시설 ID({fclty_id})에 등록된 adres(주소)가 비어있음")
                else:
                    print(f"[시설 API 응답 오류] HTTP {f_res.status_code}")
            except Exception as f_err:
                     print(f"⚠️ 시설 주소 파싱 중 오류: {f_err}")

        # [특수 처리] 공연장 명칭 괄호 제거 (네이버 지도 검색 정확도 향상)
        raw_fac_name = get_txt('fcltynm')
        fac_name = raw_fac_name

        # 중복 괄호 문구가 반복될 경우 첫 번째 패턴만 채택
        if fac_name.count('(') > 1 and ') (' in fac_name:
            parts = fac_name.split(') (')
            fac_name = parts[0] + ')'
      
        # 순수 정제 공연장명 추출 (괄호 및 잔여 특수문자 전면 제거)
        temp_name = re.sub(r'[\(\[\{].*?[\)\]\}]', '', fac_name)
        clean_fac_name = re.sub(r'[()\[\]{}]', '', temp_name).strip()

        # 단어 연속 중복 방지 (예: "플렉스라운지 플렉스라운지" ➔ "플렉스라운지")
        words = clean_fac_name.split()
        dedup_words = []
        for w in words:
            if not dedup_words or dedup_words[-1] != w:
                dedup_words.append(w)
        clean_fac_name = " ".join(dedup_words)

        # [특수 처리] 네이버 지도 검색용 완결 키워드 (지역명 + 정제 공연장명)
        # KOPIS 도로명 주소가 있는 경우 -> 주소 앞 2단어 (예: "서울특별시 금천구" 또는 "서울특별시 마포구") 추출
        if address:
            addr_parts = address.split()
            if len(addr_parts) >=2:
                district_location = f"{addr_parts[0]} {addr_parts[1]}"
            elif len(addr_parts) == 1:
                district_location = addr_parts[0]

        # KOPIS 도로명 주소가 없는 경우 -> 기본 area 사용 (예: "서울", "대구")
        if not district_location:
            district_location = get_txt('area')

        full_location_with_name = f"{district_location} {clean_fac_name}".strip()

        # [특수 처리] 줄거리(sty) 태그 내부 HTML/텍스트 구조 파싱
        sty_elem = db.find('sty')
        sty_text = ''.join(sty_elem.itertext()).strip() if sty_elem is not None else ''

        # [특수 처리] 상세 데이터 매핑 (API 태그명 prfpfrom/prfpdfrom 호환)
        performance = {
            'perf_id': get_txt('mt20id'),                     # 공연 ID
            'title': get_txt('prfnm'),                        # 공연명
            'facility_name': fac_name,                        # 원본 공연장명 (중복 정리본)
            'clean_facility_name': clean_fac_name,            # 순수 정제 공연장명 (괄호 완벽 제거)                  
            'full_location_name': full_location_with_name,    #  [신규 추가] 화면 표기용 (예: "서울특별시 금천구 플렉스라운지" 또는 "서울 플렉스라운지")           
            'map_query': full_location_with_name,             # [신규 추가] 네이버 지도 검색용 키워드
            'address': address,                               # KOPIS 시설 상세 도로명 주소
            'start_date': get_txt('prfpfrom') or get_txt('prfpdfrom'),
            'end_date': get_txt('prfpto') or get_txt('prfpdto'),
            'cast': get_txt('prfcast'),
            'ticket_price': get_txt('pcseguidance'),
            'poster': get_txt('poster'),
            'sty': sty_text,
            'area': get_txt('area'),                          # KOPIS 기본 지역명 (예: 서울)
            'dtguidance': get_txt('dtguidance'),
            'intro_image1': db.findtext('.//styurl') or ''
        }


        # 성공 디버그 콘솔 출력
        print("\n=== KOPIS 상세 데이터 매핑 성공 ===")
        print(f"📌 [공연명]        : {performance['title']}")
        print(f"📌 [공연기간]      : {performance['start_date']} ~ {performance['end_date']}")
        print(f"📌 [공연장 원본명] : {performance['facility_name']}")
        print(f"📌 [공연장 정제명] : {performance['clean_facility_name']}")
        print(f"📌 [도로명 주소]   : {performance['address'] or '❌ 주소 데이터 없음 (시설명 대체)'}\n")

        return render_template('detail.html', perf_id=perf_id, performance=performance)

    except requests.exceptions.Timeout:
        # KOPIS 서버 타임아웃 예외 처리
        print(f"❌ [상세 API 호출 실패] 공연 ID: {perf_id} | KOPIS 서버 응답 시간 초과")
        abort(500, description="공연 정보 서버 응답 시간이 초과되었습니다.")
    except Exception as e:
        # 파싱 및 기타 시스템 예외 처리
        print(f"❌ [상세 API 처리 실패] 공연 ID: {perf_id} | 원인: {e}")
        abort(500, description="공연 상세 정보를 불러오는 도중 오류가 발생했습니다.")


# # 3. 회원가입
# @main_bp.route('/register', methods=['GET'])
# def register():
#     form = UserCreateForm() # form 객체를 넘겨주어야 register.html이 정상 렌더링됨
#     return render_template('auth/register.html', form=form)

# # 4. 로그인
# @main_bp.route('/login')
# def login():
#     return render_template('login.html')

# 5. 예매 내역 (통합 내역 목록 + 티켓 확인증 모달 팝업)
@main_bp.route('/mypage/orders')
def my_orders():
    return render_template('orders.html')

# 6. term n condition 과 policy
@main_bp.route('/terms')
def terms():
    return render_template('termsNconditions.html')

# 개인정보처리방침
@main_bp.route('/privacy')
def privacy():
    return render_template('privacy_policy.html')

# 1:1 문의
@main_bp.route('/inquiry')
def inquiry():
    return render_template('inquiry.html')

# 가격 별 정보 수집
def process_single_performance(perf, price_param):
    """단일 공연 정보를 받아 가격을 파싱하고 조건에 맞는지 검증하는 함수"""
    perf_id = perf.get('mt20id')
    if not perf_id:
        return None

    try:
        detail_url = f"http://www.kopis.or.kr/openApi/restful/pblprfr/{perf_id}"
        res = requests.get(detail_url, params={'service': KOPIS_API_KEY}, timeout=2)
        if res.status_code != 200:
            return None

        root = ET.fromstring(res.content)
        db = root.find('db')
        if db is None:
            return None

        pcse = (db.findtext('pcseguidance') or '').strip()
        
        # '원' 앞의 숫자를 추출
        raw_prices = re.findall(r'([\d,]+)\s*원', pcse)
        prices = [int(p.replace(',', '')) for p in raw_prices if int(p.replace(',', '')) >= 1000]
        min_price = min(prices) if prices else 0

        if min_price == 0:
            return None

        # 조건 검증
        is_target = False
        if price_param == '10k' and min_price <= 10000:
            is_target = True
        elif price_param == '10k-30k' and 10000 < min_price < 30000:
            is_target = True
        elif price_param == '30k' and min_price >= 30000:
            is_target = True

        if is_target:
            poster_url = perf.get('poster', '')
            if poster_url and not poster_url.startswith('http'):
                poster_url = f"http://www.kopis.or.kr{poster_url}"

            return {
                'mt20id': perf_id,
                'prfnm': perf.get('prfnm'),
                'prfpd': f"{perf.get('prfpdfrom')} ~ {perf.get('prfpdto')}",
                'poster': poster_url,
                'pcse': pcse or f"{min_price:,}원"
            }
    except Exception as e:
        print(f"가격 파싱 오류 ({perf_id}): {e}")
        return None

@main_bp.route('/api/tickets/price')
def api_tickets_by_price():
    price_param = request.args.get('price', '10k')
    raw_performances = get_kopis_performances(rows='100')
    filtered_results = []

    # 멀티스레딩 적용 (10개의 스레드로 병렬 처리)
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 50개 요청을 작업 큐에 동시에 제출
        futures = [
            executor.submit(process_single_performance, perf, price_param) 
            for perf in raw_performances
        ]
        
        # 완료되는 대로 즉시 수집
        for future in as_completed(futures):
            result = future.result()
            if result:
                filtered_results.append(result)
                # 목표 개수(6개)가 채워지면 즉시 중단하여 추가 대기 시간 최소화
                if len(filtered_results) >= 6:
                    break

    return jsonify(filtered_results)