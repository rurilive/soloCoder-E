from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Tool, ToolLoan, Community, PointsLog, User
from app import db

tool_lend = Blueprint('tool_lend', __name__)


@tool_lend.route('/tools')
def list():
    community_id = request.args.get('community_id')
    category = request.args.get('category')
    status = request.args.get('status', 'available')
    
    query = Tool.query.filter_by(status=status)
    
    if community_id:
        query = query.filter_by(community_id=community_id)
    if category:
        query = query.filter_by(category=category)
    
    tools = query.order_by(Tool.created_at.desc()).all()
    communities = Community.query.all()
    categories = ['家用工具', '园艺工具', '厨房工具', '运动器材', '其他']
    
    return render_template('tools/list.html',
                         tools=tools,
                         communities=communities,
                         categories=categories,
                         current_status=status)


@tool_lend.route('/tools/<int:id>')
def detail(id):
    tool = Tool.query.get_or_404(id)
    current_loan = None
    
    if tool.status == 'loaned':
        current_loan = ToolLoan.query.filter_by(
            tool_id=id, status='active'
        ).first()
    
    return render_template('tools/detail.html',
                         tool=tool,
                         current_loan=current_loan)


@tool_lend.route('/tools/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.community_id:
        flash('请先加入小区', 'error')
        return redirect(url_for('auth.profile'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        deposit = float(request.form.get('deposit', 0))
        points_required = int(request.form.get('points_required', 0))
        
        if not name:
            flash('请填写工具名称', 'error')
            return redirect(url_for('tool_lend.create'))
        
        tool = Tool(
            name=name,
            description=description,
            category=category,
            deposit=deposit,
            points_required=points_required,
            owner_id=current_user.id,
            community_id=current_user.community_id
        )
        
        db.session.add(tool)
        db.session.commit()
        
        flash('工具发布成功', 'success')
        return redirect(url_for('tool_lend.detail', id=tool.id))
    
    communities = Community.query.all()
    categories = ['家用工具', '园艺工具', '厨房工具', '运动器材', '其他']
    return render_template('tools/create.html', 
                         communities=communities,
                         categories=categories)


@tool_lend.route('/tools/<int:id>/borrow', methods=['POST'])
@login_required
def borrow(id):
    tool = Tool.query.get_or_404(id)
    
    if tool.status != 'available':
        flash('该工具当前不可借', 'error')
        return redirect(url_for('tool_lend.detail', id=id))
    
    if tool.owner_id == current_user.id:
        flash('不能借自己的工具', 'error')
        return redirect(url_for('tool_lend.detail', id=id))
    
    if tool.points_required > current_user.points:
        flash('积分不足，无法借用', 'error')
        return redirect(url_for('tool_lend.detail', id=id))
    
    days = int(request.form.get('days', 7))
    expected_return_date = datetime.utcnow() + timedelta(days=days)
    
    loan = ToolLoan(
        tool_id=id,
        borrower_id=current_user.id,
        expected_return_date=expected_return_date
    )
    
    tool.status = 'loaned'
    tool.current_borrower_id = current_user.id
    
    db.session.add(loan)
    db.session.commit()
    
    flash('工具借用成功', 'success')
    return redirect(url_for('tool_lend.detail', id=id))


@tool_lend.route('/tools/<int:id>/return', methods=['POST'])
@login_required
def return_tool(id):
    tool = Tool.query.get_or_404(id)
    loan = ToolLoan.query.filter_by(
        tool_id=id, borrower_id=current_user.id, status='active'
    ).first()
    
    if not loan:
        flash('您没有借用该工具', 'error')
        return redirect(url_for('tool_lend.detail', id=id))
    
    loan.status = 'completed'
    loan.actual_return_date = datetime.utcnow()
    
    tool.status = 'available'
    tool.current_borrower_id = None
    
    db.session.commit()
    
    flash('工具已归还', 'success')
    return redirect(url_for('tool_lend.detail', id=id))


@tool_lend.route('/tools/<int:id>/rate', methods=['POST'])
@login_required
def rate(id):
    tool = Tool.query.get_or_404(id)
    loan = ToolLoan.query.filter_by(tool_id=id).order_by(ToolLoan.id.desc()).first()
    
    if not loan:
        flash('没有找到相关记录', 'error')
        return redirect(url_for('tool_lend.detail', id=id))
    
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')
    rating_type = request.form.get('rating_type')
    
    if rating_type == 'borrower' and current_user.id == tool.owner_id:
        loan.borrower_rating = rating
        loan.borrower_comment = comment
        
        if loan.points_required and loan.status == 'completed':
            points_change = tool.points_required
            current_user.points += points_change
            
            points_log = PointsLog(
                user_id=current_user.id,
                points_change=points_change,
                balance_after=current_user.points,
                reason='出借工具获得积分',
                related_type='tool_loan',
                related_id=loan.id
            )
            
            db.session.add(points_log)
    
    elif rating_type == 'owner' and current_user.id == loan.borrower_id:
        loan.owner_rating = rating
        loan.owner_comment = comment
        
        if tool.points_required > 0 and loan.status == 'completed':
            points_change = -tool.points_required
            if current_user.points + points_change >= 0:
                current_user.points += points_change
                
                points_log = PointsLog(
                    user_id=current_user.id,
                    points_change=points_change,
                    balance_after=current_user.points,
                    reason='借用工具支付积分',
                    related_type='tool_loan',
                    related_id=loan.id
                )
                
                db.session.add(points_log)
    
    db.session.commit()
    flash('评价已提交', 'success')
    return redirect(url_for('tool_lend.detail', id=id))
