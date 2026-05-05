from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Community
from app import db

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        community_id = request.form.get('community_id')
        
        if not all([username, password]):
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('auth.register'))
        
        if email and User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(
            username=username,
            email=email if email else None,
            phone=phone,
            community_id=community_id if community_id else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    communities = Community.query.all()
    return render_template('auth/register.html', communities=communities)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('用户名或密码错误', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=bool(remember))
        flash('登录成功', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))
    
    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('main.index'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        community_id = request.form.get('community_id')
        
        if User.query.filter_by(username=username).filter(User.id != current_user.id).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('auth.profile'))
        
        current_user.username = username
        current_user.phone = phone
        if community_id:
            current_user.community_id = community_id
        
        db.session.commit()
        flash('个人信息更新成功', 'success')
        return redirect(url_for('auth.profile'))
    
    communities = Community.query.all()
    return render_template('auth/profile.html', communities=communities)


@auth.route('/verify_community', methods=['POST'])
@login_required
def verify_community():
    if current_user.community_id:
        current_user.verification_status = 'pending'
        db.session.commit()
        flash('小区认证申请已提交，请等待审核', 'success')
    else:
        flash('请先选择小区', 'error')
    
    return redirect(url_for('auth.profile'))
