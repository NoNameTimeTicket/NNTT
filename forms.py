from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, EqualTo, Email
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, EmailField

# 회원가입 폼 클래스
class UserCreateForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired(), Length(min=3, max=25)])
    password1 = PasswordField('비밀번호', validators=[
        DataRequired(),
        EqualTo('password2', message='비밀번호가 일치하지 않습니다.')
    ])
    password2 = PasswordField('비밀번호 확인', validators=[DataRequired()])
    email = EmailField('이메일', validators=[DataRequired(), Email()])
    phone = StringField('전화번호', validators=[DataRequired(), Length(max=20)])
    address = StringField('주소', validators=[DataRequired(), Length(max=200)])

# 로그인 폼 클래스
class UserLoginForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
