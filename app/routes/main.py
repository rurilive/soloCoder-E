from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import GroupBuy, Tool, DogWalk, Community
from app import db

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    group_buys = GroupBuy.query.filter_by(status='recruiting').limit(5).all()
    tools = Tool.query.filter_by(status='available').limit(5).all()
    dog_walks = DogWalk.query.filter_by(status='open').limit(5).all()
    
    return render_template('index.html', 
                         group_buys=group_buys,
                         tools=tools,
                         dog_walks=dog_walks)


@main.route('/dashboard')
@login_required
def dashboard():
    user_group_buys = GroupBuy.query.filter_by(creator_id=current_user.id).all()
    user_tools = Tool.query.filter_by(owner_id=current_user.id).all()
    user_dog_walks = DogWalk.query.filter_by(creator_id=current_user.id).all()
    
    return render_template('dashboard.html',
                         group_buys=user_group_buys,
                         tools=user_tools,
                         dog_walks=user_dog_walks)
