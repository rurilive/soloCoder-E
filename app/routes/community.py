from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Community, User
from app import db

community = Blueprint('community', __name__)


@community.route('/communities')
def list():
    communities = Community.query.order_by(Community.name).all()
    return render_template('community/list.html', communities=communities)


@community.route('/communities/<int:id>')
def detail(id):
    community = Community.query.get_or_404(id)
    users = User.query.filter_by(community_id=id, is_verified=True).limit(10).all()
    return render_template('community/detail.html', community=community, users=users)


@community.route('/communities/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        city = request.form.get('city')
        province = request.form.get('province')
        
        if not name:
            flash('请填写小区名称', 'error')
            return redirect(url_for('community.create'))
        
        if Community.query.filter_by(name=name).first():
            flash('该小区已存在', 'error')
            return redirect(url_for('community.create'))
        
        community = Community(
            name=name,
            address=address,
            city=city,
            province=province
        )
        
        db.session.add(community)
        db.session.commit()
        
        flash('小区创建成功', 'success')
        return redirect(url_for('community.detail', id=community.id))
    
    return render_template('community/create.html')
