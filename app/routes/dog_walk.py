from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import DogWalk, Community, PointsLog
from app import db

dog_walk = Blueprint('dog_walk', __name__)


@dog_walk.route('/dog_walks')
def list():
    community_id = request.args.get('community_id')
    status = request.args.get('status', 'open')
    
    query = DogWalk.query.filter_by(status=status)
    
    if community_id:
        query = query.filter_by(community_id=community_id)
    
    dog_walks = query.order_by(DogWalk.walk_date.desc()).all()
    communities = Community.query.all()
    
    return render_template('dog_walk/list.html',
                         dog_walks=dog_walks,
                         communities=communities,
                         current_status=status)


@dog_walk.route('/dog_walks/<int:id>')
def detail(id):
    dog_walk = DogWalk.query.get_or_404(id)
    return render_template('dog_walk/detail.html', dog_walk=dog_walk)


@dog_walk.route('/dog_walks/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.community_id:
        flash('请先加入小区', 'error')
        return redirect(url_for('auth.profile'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        dog_name = request.form.get('dog_name')
        dog_breed = request.form.get('dog_breed')
        dog_age = request.form.get('dog_age')
        dog_size = request.form.get('dog_size')
        walk_date_str = request.form.get('walk_date')
        duration_minutes = int(request.form.get('duration_minutes', 30))
        meeting_location = request.form.get('meeting_location')
        points_reward = int(request.form.get('points_reward', 10))
        
        try:
            walk_date = datetime.strptime(walk_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('日期格式错误', 'error')
            return redirect(url_for('dog_walk.create'))
        
        if walk_date < datetime.utcnow():
            flash('遛狗时间不能早于当前时间', 'error')
            return redirect(url_for('dog_walk.create'))
        
        dog_walk = DogWalk(
            title=title,
            description=description,
            dog_name=dog_name,
            dog_breed=dog_breed,
            dog_age=int(dog_age) if dog_age else None,
            dog_size=dog_size,
            walk_date=walk_date,
            duration_minutes=duration_minutes,
            meeting_location=meeting_location,
            points_reward=points_reward,
            creator_id=current_user.id,
            community_id=current_user.community_id
        )
        
        db.session.add(dog_walk)
        db.session.commit()
        
        flash('遛狗互助发布成功', 'success')
        return redirect(url_for('dog_walk.detail', id=dog_walk.id))
    
    communities = Community.query.all()
    sizes = [('small', '小型犬'), ('medium', '中型犬'), ('large', '大型犬')]
    return render_template('dog_walk/create.html', 
                         communities=communities,
                         sizes=sizes)


@dog_walk.route('/dog_walks/<int:id>/accept', methods=['POST'])
@login_required
def accept(id):
    dog_walk = DogWalk.query.get_or_404(id)
    
    if dog_walk.status != 'open':
        flash('该遛狗请求已被接受或取消', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    if dog_walk.creator_id == current_user.id:
        flash('不能接受自己的遛狗请求', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    dog_walk.status = 'accepted'
    dog_walk.helper_id = current_user.id
    
    db.session.commit()
    
    flash('成功接受遛狗请求', 'success')
    return redirect(url_for('dog_walk.detail', id=id))


@dog_walk.route('/dog_walks/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    dog_walk = DogWalk.query.get_or_404(id)
    
    if dog_walk.status != 'accepted':
        flash('该遛狗请求不在进行中', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    if dog_walk.creator_id != current_user.id:
        flash('只有发布者可以标记完成', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    dog_walk.status = 'completed'
    db.session.commit()
    
    flash('遛狗已完成', 'success')
    return redirect(url_for('dog_walk.detail', id=id))


@dog_walk.route('/dog_walks/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    dog_walk = DogWalk.query.get_or_404(id)
    
    if dog_walk.creator_id != current_user.id:
        flash('只有发布者可以取消', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    if dog_walk.status not in ['open', 'accepted']:
        flash('无法取消该遛狗请求', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    dog_walk.status = 'cancelled'
    db.session.commit()
    
    flash('遛狗请求已取消', 'success')
    return redirect(url_for('dog_walk.detail', id=id))


@dog_walk.route('/dog_walks/<int:id>/rate', methods=['POST'])
@login_required
def rate(id):
    dog_walk = DogWalk.query.get_or_404(id)
    
    if dog_walk.status != 'completed':
        flash('只有完成的遛狗请求可以评价', 'error')
        return redirect(url_for('dog_walk.detail', id=id))
    
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')
    rating_type = request.form.get('rating_type')
    
    if rating_type == 'helper' and current_user.id == dog_walk.creator_id:
        dog_walk.helper_rating = rating
        dog_walk.helper_comment = comment
        
        if dog_walk.points_reward > 0:
            from app.models import User
            helper = User.query.get(dog_walk.helper_id)
            if helper:
                helper.points += dog_walk.points_reward
                
                points_log = PointsLog(
                    user_id=helper.id,
                    points_change=dog_walk.points_reward,
                    balance_after=helper.points,
                    reason='遛狗互助获得积分',
                    related_type='dog_walk',
                    related_id=dog_walk.id
                )
                
                db.session.add(points_log)
                
                helper.total_helps += 1
                
                if helper.reputation_score:
                    helper.reputation_score = (helper.reputation_score + rating) / 2
                else:
                    helper.reputation_score = rating
    
    elif rating_type == 'creator' and current_user.id == dog_walk.helper_id:
        dog_walk.creator_rating = rating
        dog_walk.creator_comment = comment
    
    db.session.commit()
    flash('评价已提交', 'success')
    return redirect(url_for('dog_walk.detail', id=id))
