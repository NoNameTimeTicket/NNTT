from init_db import db
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from forms import UserCreateForm, UserLoginForm
from table_model import User
import functools

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register(): # 회원등록 담당
    form = UserCreateForm()
    print(f"way = {request.method}")

    if form.validate_on_submit():
        print(f"validate_on_submit")

    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print(f"user_info = {user}")
        if not user:
            user = User(username=form.username.data,
                        password=generate_password_hash(form.password1.data),
                        email=form.email.data,
                        phone=form.phone.data,
                        address=form.address.data
                        )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            flash('이미 존재하는 사용자입니다.')
    return render_template('register.html', form=form)

@bp.route('/login/', methods=('GET', 'POST'))
def login():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            error = "존재하지 않는 사용자입니다."
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 올바르지 않습니다."
        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        flash(error)
    return render_template('login.html', form=form)

# 로그아웃 라우트 함수
@bp.route('/logout/')
def logout():
    session.clear() # session 삭제
    return redirect(url_for('main.index')) #main.index로 복귀

def login_required(view):
    # 메타데이터 유지: 데코레이터를 쓸 때 함수 이름이 전부 wrapped_view로 뭉개지는 걸 방지
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None: # g.user == none 유저 로그인이 안되어 있을때 로그인 페이지로 이동
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped_view

# 어떤 라우트 함수가 실행되든 사전에 세션을 검사하여 로그인한 사용자의 DB 객체를 g.user 변수 상시 적재
# request 이전에 작동시킬 함수정의
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)