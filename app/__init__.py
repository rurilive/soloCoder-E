from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.group_buy import group_buy
    from app.routes.tool_lend import tool_lend
    from app.routes.dog_walk import dog_walk
    from app.routes.community import community
    from app.routes.verification import verification

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(group_buy)
    app.register_blueprint(tool_lend)
    app.register_blueprint(dog_walk)
    app.register_blueprint(community)
    app.register_blueprint(verification)

    with app.app_context():
        db.create_all()
        init_admin_user(app)

    return app


def init_admin_user(app):
    from app.models import User
    
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    admin_password = app.config.get('ADMIN_PASSWORD', 'Admin123!')
    
    existing_admin = User.query.filter_by(username=admin_username).first()
    if existing_admin:
        return
    
    admin = User(
        username=admin_username,
        is_verified=True,
        verification_status='verified',
        is_admin=True,
        points=1000,
        reputation_score=5.0
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    
    app.logger.info(f'Admin user created: {admin_username}')
