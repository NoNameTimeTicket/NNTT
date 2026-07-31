### 임시 파일 ###
from flask import Blueprint, render_template, request

main_bp = Blueprint('main', __name__)

# 1. 메인 (통합검색 + 상단 GNB + 장르별 탭 + 공연 목록)
@main_bp.route('/')
def index():
    search_query = request.args.get('q', '') # 검색어 수집
    genre_tab = request.args.get('genre', 'all') # 장르 탭 수집
    return render_template('index.html', query=search_query, current_genre=genre_tab)

# 2. 공연 상세 (공통 상세페이지 + 회차 예매 모달 + 공연 후기 게시판)
@main_bp.route('/performances/<int:perf_id>')
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