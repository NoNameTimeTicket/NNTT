from flask import Blueprint, render_template, url_for, redirect, request, g, flash, current_app
from table_model import Notice, User
from forms import NoticeForm
from datetime import datetime
from init_db import db
import os
from views.auth_views import login_required

bp = Blueprint('notice', __name__, url_prefix='/notice')

# 공통으로 사용하는 내용을 변수화
per_page_num = 10
default_page = 1

@bp.route('/list/')
def _list():
    # 현재 페이지 번호 가져오기 (기본값은 1)
    page = request.args.get('page', type=int, default=default_page)
    kw = request.args.get('kw', type=str, default='')   # 검색어

    # 기본 쿼리
    Notice_list = Notice.query

    # 2. 검색 (kw) 조건 처리
    if kw:
        search = '%%{}%%'.format(kw)

        Notice_list = (Notice_list 
            .filter(Notice.subject.ilike(search) |
                    Notice.content.ilike(search) |
                    Notice.user.has(User.username.ilike(search))))
        
    else:  # recent (최신순)
        Notice_list = (Notice_list
        .group_by(Notice.id)
        .order_by(Notice.create_date.desc()))

    # 데이터베이스의 Question 테이블에서 모든 질문 데이터를 가져온다
    # 작성일(create_date)의 역순(desc - 최신순)으로 정렬하여 Notice_list 변수에 담는다. + 한 페이지당 개수를 조회하는 기능 추가(paginate)
    Notice_list = Notice_list.paginate(page=page, per_page=per_page_num)
    # 공지사항 목록(Notice_list) 데이터를 템플릿(HTML) 파일에 전달하며 화면을 그린다(렌더링)
    return render_template('support/notice_list.html', notice_list=Notice_list, page=page, kw=kw)

@bp.route('/detail/<int:notice_id>/')
def detail(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    return render_template('support/notice_detail.html', notice=notice)

# 공지 등록 라우트 함수 추가
@bp.route('/create/', methods=('GET', 'POST'))
@login_required # 해당 메서드 만족해야 def create() 실행가능
def create():
    form = NoticeForm()
    if request.method == 'POST' and form.validate_on_submit():
        # 등록할 내용을 Notice table에 넣어서 등록한다
        add_port_notice = Notice(subject=form.subject.data, content=form.content.data, create_date=datetime.now(), user= g.user)
        
        db.session.add(add_port_notice)
        db.session.commit()
        return redirect(url_for('notice._list'))
    return render_template('support/notice_form.html', form=form)

@bp.route('/modify/<int:notice_id>/', methods=('GET', 'POST'))
@login_required
def modify(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if g.user.username != 'admin':
        flash('수정권한이 없습니다')
        return redirect(url_for('notice.detail', notice_id=notice_id))

    if request.method == 'POST':
        form = NoticeForm()
        if form.validate_on_submit():
            form.populate_obj(notice)
            db.session.commit()
            return redirect(url_for('notice.detail', notice_id=notice_id))
    else:
        # GET 요청일 경우 기존 데이터를 폼에 채워서 렌더링
        form = NoticeForm(obj=notice)
    return render_template('support/notice_form.html', form=form)

@bp.route('/delete/<int:notice_id>/')
@login_required
def delete(notice_id):
    notice = Notice.query.get_or_404(notice_id)

    if g.user.username == 'admin':
        db.session.delete(notice)
        db.session.commit()
    else:
        flash('삭제권한이 없습니다')
        return redirect(url_for('notice.detail', notice_id=notice_id))
    return redirect(url_for('notice._list'))