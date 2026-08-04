from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, abort
import requests, re
import xml.etree.ElementTree as ET

main_bp = Blueprint('main', __name__)
KOPIS_API_KEY = "19fc20e402ce49df83b5d2f6e9d50822"

def get_kopis_performances():
    """KOPIS API를 호출하여 전체 공연 목록을 가져오는 공통 함수"""

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
        'rows': '50',
        'prfstate': '02'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        performances = []
        for db in root.findall('db'):
            performances.append({
                'mt20id': db.findtext('mt20id'),
                'prfnm': db.findtext('prfnm'),
                'genrenm': db.findtext('genrenm'),
                'prfpdfrom': db.findtext('prfpdfrom'),
                'prfpdto': db.findtext('prfpdto'),
                'poster': db.findtext('poster'),
                'fcltynm': db.findtext('fcltynm')
            })
        return performances
    except Exception as e:
        print(f"API 요청 실패: {e}")
        return []

# 메인 (통합검색 + 상단 GNB + 장르별 탭 + 공연 목록)
@main_bp.route('/')
def index():
    search_query = request.args.get('q', '') # 검색어 수집
    genre_tab = request.args.get('genre', 'all') # 장르 탭 수집
    return render_template('index.html', query=search_query, current_genre=genre_tab)

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

# 연극 전용 페이지
@main_bp.route('/performances/play')
def play_list():
    all_perfs = get_kopis_performances()
    plays = [p for p in all_perfs if p.get('genrenm') == '연극']
    return render_template('play.html', performances=plays)

# 콘서트 목록 페이지
@main_bp.route('/performances/concert')
def concert_list():
    all_perfs = get_kopis_performances()
    # KOPIS에서 대중음악/대중콘서트/음악 등으로 들어올 수 있어 포함 여부 체크
    concerts = [p for p in all_perfs if '콘서트' in p.get('genrenm', '') or '음악' in p.get('genrenm', '')]
    return render_template('concert.html', performances=concerts)

# 2. 공연 상세 (공통 상세페이지 + 회차 예매 모달 + 공연 후기 게시판)
# 1) 상세페이지 수정 2026-08-04 박근수
@main_bp.route('/performances/<string:perf_id>')
def performance_detail(perf_id):
    #수정버젼 2026-08-04 박근수
    # 1. KOPIS API URL 및 파라미터 설정
    url = f"http://www.kopis.or.kr/openApi/restful/pblprfr/{perf_id}"
    params = {'service' : KOPIS_API_KEY}

    try:
        # 2. API 호출
        response = requests.get(url, params=params)

        if response.status_code !=200:
            abort(500, description="KOPIS API 호출 실패")

        # 3. ElementTree를 활용한 XML 파싱 (외부 라이브러리 미사용)
        root = ET.fromstring(response.text)
        db_elem = root.find('db')

        if db_elem is None:
            abort(404, description="해당 공연 정보를 찾을 수 없습니다.")

        # XML 태그 텍스트를 안전하게 가져오는 헬퍼 함수
        def get_tag_text(tag_name):
            elem = db_elem.find(tag_name)
            return elem.text if elem is not None and elem.text else ''

        # 줄거리(sty) 태그 안의 모든 텍스트/HTML을 파싱하는 함수 추가
        def get_sty_text():
            sty_elem = db_elem.find('sty')
            if sty_elem is not None:
                ## itertext()로 sty 내부 하위 태그들까지 모든 텍스트를 다 합쳐서 가져옴
                return ''.join(sty_elem.itertext()).strip()
            return ''
 
        # 💡 [추가] 공연시설 ID(fcltyid) 추출 및 시설 상세 API 호출로 주소 가져오기
        fclty_id = get_tag_text('fcltyid')
        facility_address = ''

        if fclty_id:
            try:
                fclty_url = f"http://www.kopis.or.kr/openApi/restful/prfcom/{fclty_id}"
                fclty_res = requests.get(fclty_url, params={'service': KOPIS_API_KEY}, timeout=3)
                if fclty_res.satus_code == 200:
                    fclty_root = ET.fromstring(fclty_res.text)
                    # KOPIS 시설 상세 XML root의 db 태그 접근
                    fclty_db =fclty_root.find('db')
                    if fclty_db is not None:
                        adres_elem = fclty_db.find('adres')
                        if adres_elem is not None and adres_elem.text:
                           facility_address = adres_elem.text.strip()
            except Exception as fclty_err:
               print(f"시설 주소 조회 실패: {fclty_err}")


        # 수정 시설명 괄호 제거 정제 (예: "어울아트센터(구. 대구북구문예회관)..." -> "어울아트센터")
        raw_facility_name = get_tag_text('fcltynm')
        clean_name = re.sub(r'\([^)]*\)', '', raw_facility_name)
        clean_facility_name = re.sub(r'[()\[\]]', '', clean_name).strip()              
        

        # 소개이미지 목록 (styurls > styurl) 추출
        intro_image1 = ''
        styurls_elem = db_elem.find('styurls')
        if styurls_elem is not None:
            first_styurl = styurls_elem.find('styurl')
            if first_styurl is not None and first_styurl.text:
                intro_image1 = first_styurl.text

        # 상세 데이터 매핑
        performance = {
            'perf_id': get_tag_text('mt20id'),         # 공연ID
            'title': get_tag_text('prfnm'),           # 공연명
            'facility_name': raw_facility_name,       # 화면표기용(원본)
            'clean_facility_name': clean_facility_name, # 지도 검색 전용 정제 명칭
            'address': facility_address,              # 도로명 주소
            'start_date': get_tag_text('prfpfrom'),   # 공연시작일
            'end_date': get_tag_text('prfpto'),       # 공연종료일
            'cast': get_tag_text('prfcast'),          # 공연출연진
            'ticket_price': get_tag_text('pcseguidance'), # 티켓가격
            'poster': get_tag_text('poster'),         # 포스터이미지경로
            'sty': get_sty_text(),               # 줄거리
            'area': get_tag_text('area'),             # 지역
            'hall_name': get_tag_text('fcltynm'),     # 공연장
            'dtguidance': get_tag_text('dtguidance'), # 공연시간
            'intro_image1': intro_image1               # 소개이미지1
        }

#  디버깅용 로그: 콘솔 창에 실제로 어떤 데이터가 들어왔는지 확인합니다.
        print("\n==========================================")
        print("=== KOPIS 상세 데이터 매핑 디버깅 결과 ===")
        print("==========================================")
        print(f"📌 [공연명]          : {performance.get('title')}")
        print(f"📌 [공연시설 ID]     : {fclty_id}")
        print(f"📌 [공연장 원본명]   : {performance.get('facility_name')}")
        print(f"📌 [공연장 정제명]   : {performance.get('clean_facility_name')} (<- 네이버 지도 검색용)")
        print(f"📌 [KOPIS 도로명주소]: {performance.get('address') or '❌ 주소 데이터 없음 (시설명으로 대체)'}")
        print("------------------------------------------")
        
        # 전체 딕셔너리 항목 요약 출력 (기존 로직 유지 및 EMPYT 오타 교정)
        for key, val in performance.items():
            val_str = str(val) if val else 'EMPTY'
            print(f"{key:<20}: {val_str[:30]}")
        print("==========================================\n")

        return render_template('detail.html', perf_id=perf_id, performance=performance)
    
    except Exception as e:
        print(f"공연 상세정보 조회 중 오류 발생: {e}")
        abort(500, description="공연 정보를 불러오는 중 오류가 발생했습니다.")

# 3. 회원가입
@main_bp.route('/register')
def register():
    return render_template('register.html')

# 4. 로그인
@main_bp.route('/login')
def login():
    return render_template('login.html')

# 5. 예매 내역 (통합 내역 목록 + 티켓 확인증 모달 팝업)
@main_bp.route('/mypage/orders')
def my_orders():
    return render_template('orders.html')