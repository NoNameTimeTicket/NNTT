from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
import requests
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
@main_bp.route('/performances/<string:perf_id>')
def performance_detail(perf_id):
    return render_template('detail.html', perf_id=perf_id)

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