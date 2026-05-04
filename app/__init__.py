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

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(group_buy)
    app.register_blueprint(tool_lend)
    app.register_blueprint(dog_walk)
    app.register_blueprint(community)

    with app.app_context():
        db.create_all()

    return app
