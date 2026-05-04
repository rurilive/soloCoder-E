from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import GroupBuy, GroupBuyParticipant, Community
from app import db

group_buy = Blueprint('group_buy', __name__)


@group_buy.route('/group_buy')
def list():
    community_id = request.args.get('community_id')
    status = request.args.get('status', 'recruiting')
    
    query = GroupBuy.query.filter_by(status=status)
    
    if community_id:
        query = query.filter_by(community_id=community_id)
    
    group_buys = query.order_by(GroupBuy.created_at.desc()).all()
    communities = Community.query.all()
    
    return render_template('group_buy/list.html', 
                         group_buys=group_buys,
                         communities=communities,
                         current_status=status)


@group_buy.route('/group_buy/<int:id>')
def detail(id):
    group_buy = GroupBuy.query.get_or_404(id)
    participants = GroupBuyParticipant.query.filter_by(group_buy_id=id).all()
    
    user_participant = None
    if current_user.is_authenticated:
        user_participant = GroupBuyParticipant.query.filter_by(
            group_buy_id=id, user_id=current_user.id
        ).first()
    
    return render_template('group_buy/detail.html',
                         group_buy=group_buy,
                         participants=participants,
                         user_participant=user_participant)


@group_buy.route('/group_buy/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.community_id:
        flash('请先加入小区', 'error')
        return redirect(url_for('auth.profile'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        min_participants = int(request.form.get('min_participants', 5))
        max_participants = request.form.get('max_participants')
        price_per_person = float(request.form.get('price_per_person'))
        deadline_str = request.form.get('deadline')
        delivery_date_str = request.form.get('delivery_date')
        pickup_location = request.form.get('pickup_location')
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%dT%H:%M') if delivery_date_str else None
        except ValueError:
            flash('日期格式错误', 'error')
            return redirect(url_for('group_buy.create'))
        
        if delivery_date and delivery_date < deadline:
            flash('配送日期不能早于截止日期', 'error')
            return redirect(url_for('group_buy.create'))
        
        group_buy = GroupBuy(
            title=title,
            description=description,
            category=category,
            min_participants=min_participants,
            max_participants=int(max_participants) if max_participants else None,
            price_per_person=price_per_person,
            deadline=deadline,
            delivery_date=delivery_date,
            pickup_location=pickup_location,
            creator_id=current_user.id,
            community_id=current_user.community_id
        )
        
        db.session.add(group_buy)
        db.session.commit()
        
        flash('拼团创建成功', 'success')
        return redirect(url_for('group_buy.detail', id=group_buy.id))
    
    communities = Community.query.all()
    return render_template('group_buy/create.html', communities=communities)


@group_buy.route('/group_buy/<int:id>/join', methods=['POST'])
@login_required
def join(id):
    group_buy = GroupBuy.query.get_or_404(id)
    
    if group_buy.status != 'recruiting':
        flash('该拼团已不在招募中', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    if datetime.utcnow() > group_buy.deadline:
        flash('拼团已截止', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    existing_participant = GroupBuyParticipant.query.filter_by(
        group_buy_id=id, user_id=current_user.id
    ).first()
    
    if existing_participant:
        flash('您已参与该拼团', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    if group_buy.max_participants and group_buy.current_participants >= group_buy.max_participants:
        flash('拼团人数已满', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    quantity = int(request.form.get('quantity', 1))
    total_price = group_buy.price_per_person * quantity
    
    participant = GroupBuyParticipant(
        group_buy_id=id,
        user_id=current_user.id,
        quantity=quantity,
        total_price=total_price
    )
    
    group_buy.current_participants += 1
    
    db.session.add(participant)
    db.session.commit()
    
    flash('成功加入拼团', 'success')
    return redirect(url_for('group_buy.detail', id=id))


@group_buy.route('/group_buy/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_participation(id):
    group_buy = GroupBuy.query.get_or_404(id)
    
    participant = GroupBuyParticipant.query.filter_by(
        group_buy_id=id, user_id=current_user.id
    ).first()
    
    if not participant:
        flash('您未参与该拼团', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    if group_buy.status != 'recruiting':
        flash('拼团已结束，无法取消', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    db.session.delete(participant)
    group_buy.current_participants -= 1
    db.session.commit()
    
    flash('已取消参与拼团', 'success')
    return redirect(url_for('group_buy.detail', id=id))


@group_buy.route('/group_buy/<int:id>/start', methods=['POST'])
@login_required
def start(id):
    group_buy = GroupBuy.query.get_or_404(id)
    
    if group_buy.creator_id != current_user.id:
        flash('您不是该拼团的创建者', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    if group_buy.current_participants < group_buy.min_participants:
        flash('参团人数不足，无法成团', 'error')
        return redirect(url_for('group_buy.detail', id=id))
    
    group_buy.status = 'active'
    db.session.commit()
    
    flash('拼团已开始', 'success')
    return redirect(url_for('group_buy.detail', id=id))
